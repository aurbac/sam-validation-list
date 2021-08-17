FROM public.ecr.aws/bitnami/python:latest

WORKDIR /usr/src/app

# Copy function code
COPY . .

# Install the function's dependencies using file requirements.txt
# from your project folder.

RUN  pip3 install -r requirements.txt --target /usr/src/app

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "python", "./app.py" ]