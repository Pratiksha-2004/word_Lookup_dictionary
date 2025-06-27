import requests
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LogoutView
from django.urls import reverse_lazy
from .models import SearchHistory
from .forms import RegisterForm, LoginForm

def home(request):
    return render(request, 'dictionary_app/home.html')

def search_word(request):
    query = request.GET.get("word", "").strip()
    if not query:
        return JsonResponse({"error": "Please provide a word to search."}, status=400)

    dictionary_api = f"https://api.dictionaryapi.dev/api/v2/entries/en/{query}"
    datamuse_syn = f"https://api.datamuse.com/words?rel_syn={query}"
    datamuse_ant = f"https://api.datamuse.com/words?rel_ant={query}"

    try:
        dict_res = requests.get(dictionary_api)
        if dict_res.status_code != 200:
            return JsonResponse({"error": f"Word '{query}' not found."}, status=404)
        dict_data = dict_res.json()[0]

        syn_res = requests.get(datamuse_syn).json()
        ant_res = requests.get(datamuse_ant).json()

        synonyms = [item['word'] for item in syn_res]
        antonyms = [item['word'] for item in ant_res]

        meanings = []
        for meaning in dict_data.get("meanings", []):
            part_of_speech = meaning.get("partOfSpeech", "")
            definitions = meaning.get("definitions", [])
            if definitions:
                meanings.append({
                    "partOfSpeech": part_of_speech,
                    "definition": definitions[0].get("definition", "")
                })

        pronunciation = "Not available"
        audio = None
        for p in dict_data.get("phonetics", []):
            if p.get("text"):
                pronunciation = p["text"]
            if p.get("audio"):
                audio = p["audio"]
                break

        # Save to search history
        if request.user.is_authenticated:
            SearchHistory.objects.create(user=request.user, word=query)
        else:
            SearchHistory.objects.create(word=query)

        return JsonResponse({
            "word": query,
            "meanings": meanings,
            "pronunciation": pronunciation,
            "pronunciation_audio": audio,
            "synonyms": synonyms,
            "antonyms": antonyms,
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def search_history(request):
    history = SearchHistory.objects.all().order_by('-timestamp')[:10]
    data = [{"word": h.word, "searched_at": h.timestamp.strftime("%Y-%m-%d %H:%M:%S")} for h in history]
    return JsonResponse({"history": data})

def login_view(request):
    login_form = LoginForm(data=request.POST or None)
    if request.method == "POST" and login_form.is_valid():
        user = authenticate(
            request,
            username=login_form.cleaned_data["username"],
            password=login_form.cleaned_data["password"]
        )
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            login_form.add_error(None, "Invalid username or password.")
    return render(request, 'dictionary_app/login.html', {'login_form': login_form})

def register_view(request):
    reg_form = RegisterForm(request.POST or None)
    if request.method == "POST" and reg_form.is_valid():
        reg_form.save()
        return redirect('login_page')
    return render(request, 'dictionary_app/register.html', {"reg_form": reg_form})

def total_searches(request):
    total = SearchHistory.objects.count()
    return JsonResponse({"total_searches": total})

class CustomLogoutView(LogoutView):
    def get(self, request, *args, **kwargs):
        return redirect(reverse_lazy('login_page'))

    def post(self, request, *args, **kwargs):
        return redirect(reverse_lazy('login_page'))
