from django.http import HttpResponse


def home_view(request):
    return HttpResponse("Welcome to D247 APIs.")