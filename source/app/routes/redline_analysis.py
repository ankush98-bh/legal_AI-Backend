from fastapi import APIRouter, UploadFile, File, HTTPException, Response, Form, status, Request
#rom ..services.auth_service import authorize
from fastapi.responses import JSONResponse
from typing import Optional
import json
import re
from ..config import DEFAULT_MODEL
from ..services import extract_text_from_pdf, compare_texts, highlight_differences, call_ollama_api, format_response

router = APIRouter()

def generate_llm_prompt(formatted_data: dict, file2_text: str) -> str:
    prompt = "You are a legal document analyzer.You are provided with the differences between two legal documents. Review the changes and respond ONLY in JSON array format.\n\n"

    if "added" in formatted_data and isinstance(formatted_data["added"], list):
        prompt += "### Added Lines:\n"
        for idx, line_content in enumerate(formatted_data["added"], start=1):
            prompt += f"- (Added Line {idx}): {line_content}\n"
    prompt += "\n"

    if "removed" in formatted_data and isinstance(formatted_data["removed"], list):
        prompt += "### Removed Lines:\n"
        for idx, line_content in enumerate(formatted_data["removed"], start=1):
            prompt += f"- (Removed Line {idx}): {line_content}\n"
    prompt += "\n"

    if "changed_lines" in formatted_data and isinstance(formatted_data["changed_lines"], list):
        prompt += "### Changed Lines:\n"
        for change in formatted_data["changed_lines"]:
            prompt += f"Original: {change['original']['content']}\n"
            prompt += f"Modified: {change['modified']['content']}\n"
    prompt += "\n"

    if "unified_diff" in formatted_data:
        prompt += "### Unified Diff:\n"
        prompt += f"{formatted_data['unified_diff']}\n\n"

    prompt += f"Below is the extracted text from file2 for context:\n{file2_text}\n\n"
    prompt += '''You are a legal document analyzer.

Your task is to analyze a set of differences between two versions of a legal document and return your findings in a **strict JSON array**.

Each object in the array MUST contain the following depending on the change type:

---

1. For **"added"**:
- type: "added"
- line_number: (integer, required)
- content: (string, required)
- Significance: "Minor", "Major", or "None"
- description: A short legal impact analysis

2. For **"removed"**:
- type: "removed"
- line_number: (integer, required)
- content: (string, required)
- Significance: "Minor", "Major", or "None"
- description: A short legal impact analysis

3. For **"modified"**:
- type: "modified"
- line_number: (integer, required)
- original: (string, required)
- modified: (string, required)
- Significance: "Minor", "Major", or "None"
- description: A short legal impact analysis

---

⚠️ You must NEVER leave any required field as null or undefined. If the input data does not include the required field, infer it or say “Unknown - please verify manually.”

You MUST return only valid JSON — no markdown, no commentary, no extra text.
].'''

    return prompt


@router.post("/redline_analysis")
#authorize()
async def redline_analysis(
    request: Request,
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    model: Optional[str] = Form(DEFAULT_MODEL),
    deep_search: bool = Form(False),
    current_user=None
):
    try:
        if not file1.filename.endswith(".pdf") or not file2.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        text1, pdf_stream1 = extract_text_from_pdf(file1)
        text2, pdf_stream2 = extract_text_from_pdf(file2)

        text1_lines = text1.splitlines()
        text2_lines = text2.splitlines()

        # Compare documents
        comparison = compare_texts("\n".join(text1_lines), "\n".join(text2_lines))
        if deep_search:
            prompt = generate_llm_prompt(comparison, text2)
            response = await call_ollama_api("api/generate", method="POST", json_data={"model": model, "prompt": prompt, "stream": False})
            raw_response = response.get("response", "")

            # Attempt to find the JSON within the markdown code block
            json_start = raw_response.find('[')
            json_end = raw_response.rfind(']')
            if json_start != -1 and json_end != -1 and json_start < json_end:
                json_string = raw_response[json_start:json_end + 1]
                # Clean up non-standard whitespace and control characters
                #cleaned_json_string = re.sub(r'\s', ' ', json_string).replace('\\', '')  
                cleaned_json_string = re.sub(r'[^\x20-\x7E]', '', json_string)
                # print(cleaned_json_string)
                try:
                    llm_analysis = json.loads(cleaned_json_string)
                    detailed_analysis = []
                    text1_lines = text1.splitlines()
                    text2_lines = text2.splitlines()

                    for item in llm_analysis:
                        analysis_item = {"type": item.get("type").lower()}
                        if "line_number" in item:
                            analysis_item["line_number"] = item["line_number"]

                        if analysis_item["type"] == "modified":
                            original_content = item.get("original")
                            modified_content = item.get("modified")
                            analysis_item["original"] = original_content
                            analysis_item["modified"] = modified_content
                            # Try to find line numbers (can be unreliable with difflib)
                            original_line_number = text1_lines.index(original_content) + 1 if original_content in text1_lines else None
                            modified_line_number = text2_lines.index(modified_content) + 1 if modified_content in text2_lines else None
                            analysis_item["line_number"] = original_line_number or modified_line_number

                        elif analysis_item["type"] == "added":
                            analysis_item["content"] = item.get("content") or item.get("modified")

                            if "line_number" not in item or item["line_number"] is None:
                                line_number = text2_lines.index(analysis_item["content"]) + 1 if analysis_item["content"] in text2_lines else None
                                analysis_item["line_number"] = line_number

                        elif analysis_item["type"] == "removed":
                            analysis_item["content"] = item.get("content") or item.get("original")

                            if not analysis_item["content"]:
                                continue  # skip this item entirely

                            if "line_number" not in item or item["line_number"] is None:
                                line_number = text1_lines.index(analysis_item["content"]) + 1 if analysis_item["content"] in text1_lines else None
                                analysis_item["line_number"] = line_number

                        analysis_item["Significance"] = item.get("Significance")
                        analysis_item["description"] = item.get("description")
                        detailed_analysis.append(analysis_item)

                    return {"detailed_analysis": detailed_analysis}
                except json.JSONDecodeError as e:
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to decode LLM response as JSON after aggressive cleaning {e}")
            else:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not find JSON in LLM response")
        else:
            try:
                highlighted_pdf = highlight_differences(pdf_stream2, comparison)
                return Response(content=highlighted_pdf, media_type="application/pdf")
            except Exception as e:
                return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                "error": str(e),
                "error_type": type(e).__name__,
                "error_file_details": f"error on line {e.__traceback__.tb_lineno} inside {__file__}"
                })

    except Exception as e:
        return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": str(e),
            "error_type": type(e).__name__,
            "error_file_details": f"error on line {e.__traceback__.tb_lineno} inside {__file__}"
        })