# wadia-ghandy-backend

To run this code, the command is: uvicorn app:app --reload
To run with async capabilities : uvicorn app:app --workers 4

To create migrations, the command is: alembic revision --autogenerate -m "<your commit migration message>"
To apply migrations, the command is: alembic upgrade head

To check for APIs in Postman, go to Body tab and in it click on raw option in JSON format and payload will be:

{
  "domain": "domain-name",
  "sub_domain": "sub_domain-name",
  "prompt": "This prompt will be ignored.",
}

To test the APIs which have File upload option then in postman go to body tab, then select form-data option there you may upload the file and test the file. Alternatively, you may use Swagger UI to check for APIs.