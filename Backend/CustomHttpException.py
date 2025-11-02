
class CustomHttpException(Exception):
  def __init__(self, status, message, status_code):
    super().__init__(message)
    self.status_code = status_code
    self.status = status

def exception_raiser(condition, status, message, status_code):
  if condition:
    raise CustomHttpException(status, message, status_code)