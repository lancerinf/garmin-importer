FROM public.ecr.aws/lambda/python:3.10

COPY app.py aws_utils.py garmin_utils.py garmin_models.py failure_modes.py requirements.txt ./

RUN pip install -r requirements.txt

CMD ["app.lambda_handler"]
