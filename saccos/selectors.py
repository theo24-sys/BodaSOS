from dispatch.models import Sacco


def sacco_records():
    return Sacco.objects.all()
