from celery import shared_task

@shared_task
def test_task():
    print("Celery task executed")
    return "Celery is working"