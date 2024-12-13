FROM python:3.10

# copy source code to image
COPY . /app
WORKDIR /app

# install system dependencies for the project
RUN pip install pipenv

# # install from Pipfile
RUN pipenv install
# RUN mkdir logs

#CMD ["pipenv", "run", "python", "main.py"]
