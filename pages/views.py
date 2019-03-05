from django.shortcuts import render


def index(request):
    return render(request, 'pages/index.html')


def about(request):
    return render(request, 'pages/about.html')


def helpfaq(request):
    return render(request, 'pages/helpfaq.html')


def terms(request):
    return render(request, 'pages/terms.html')
