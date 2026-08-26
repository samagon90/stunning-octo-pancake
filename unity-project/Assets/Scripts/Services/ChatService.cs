using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace DreamMasters.Services
{
    /// <summary>Сообщение чата.</summary>
    [Serializable]
    public class ChatMessage
    {
        public string author;
        public string text;
        public long utcTicks;

        public override string ToString() => $"{author}: {text}";
    }

    /// <summary>Провайдер чата: локальная «жизнь мира» сейчас, REST — после деплоя сервера.</summary>
    public interface IChatProvider
    {
        Task<List<ChatMessage>> FetchAsync();
        Task<bool> SendAsync(ChatMessage message);
    }

    /// <summary>
    /// Локальный чат-заглушка: мировые реплики игроков (канон: «живое общение в чате» оригинала),
    /// свои сообщения сохраняются на сессию. После деплоя подменяется RestChatProvider.
    /// </summary>
    public class LocalChatProvider : IChatProvider
    {
        private static readonly List<ChatMessage> World = new List<ChatMessage>
        {
            new ChatMessage { author = "МастерОгня", text = "Кто на Барьеры стихий? Вода рулит." },
            new ChatMessage { author = "СнежнаяДева", text = "Прокачала Чейни до 6 звёзд — шторм ломает всё." },
            new ChatMessage { author = "ДревоЖизни", text = "Фрэнк танк номер один, меняйте моё мнение." },
            new ChatMessage { author = "Аид_на_чиле", text = "Сон Ветра на 10-м уровне — жесть. Готовьте землистов." },
            new ChatMessage { author = "ЛедиТуман", text = "Собрала 80 осколков, кому выпал Зевс?" },
            new ChatMessage { author = "Костолом", text = "Колизей: 3 победы подряд, рейтинг 1180." },
            new ChatMessage { author = "Сновидец", text = "Первый сон я проиграл 14 раз, пока не понял: так задумано))" },
        };

        private readonly List<ChatMessage> _session = new List<ChatMessage>();

        public Task<List<ChatMessage>> FetchAsync()
        {
            var all = new List<ChatMessage>(World);
            all.AddRange(_session);
            return Task.FromResult(all);
        }

        public Task<bool> SendAsync(ChatMessage message)
        {
            _session.Add(message);
            return Task.FromResult(true);
        }
    }

    /// <summary>REST-чат (Cloud Functions /chat) — включается вместе с сервером.</summary>
    public class RestChatProvider : IChatProvider
    {
        private readonly RestApiClient _api;
        public RestChatProvider(string baseUrl) { _api = new RestApiClient(baseUrl); }

        public async Task<List<ChatMessage>> FetchAsync()
        {
            var resp = await _api.GetAsync("/chat");
            if (!resp.Ok || string.IsNullOrEmpty(resp.Data)) return new List<ChatMessage>();
            try { return Parse(resp.Data); } catch { return new List<ChatMessage>(); }
        }

        public async Task<bool> SendAsync(ChatMessage message)
        {
            string json = $"{{\"author\":\"{message.author}\",\"text\":\"{message.text}\",\"utcTicks\":{message.utcTicks}}}";
            var resp = await _api.PostAsync("/chat", json);
            return resp.Ok;
        }

        private static List<ChatMessage> Parse(string json)
        {
            var list = new List<ChatMessage>();
            foreach (var obj in json.Trim('[', ']').Split("},"))
            {
                string s = obj.Trim().TrimStart('{').TrimEnd('}');
                var msg = new ChatMessage();
                foreach (var kv in s.Split(','))
                {
                    var p = kv.Split(':');
                    if (p.Length < 2) continue;
                    string key = p[0].Trim().Trim('"');
                    string val = p[1].Trim().Trim('"');
                    if (key == "author") msg.author = val;
                    else if (key == "text") msg.text = val;
                }
                if (!string.IsNullOrEmpty(msg.text)) list.Add(msg);
            }
            return list;
        }
    }

    /// <summary>Сервис чата: история + отправка + событие обновления. UI только слушает.</summary>
    public class ChatService
    {
        public readonly IChatProvider Provider;
        public readonly List<ChatMessage> History = new List<ChatMessage>();
        public event Action Updated;

        public ChatService(IChatProvider provider) { Provider = provider; }

        public async void RefreshAsync()
        {
            var messages = await Provider.FetchAsync();
            History.Clear();
            History.AddRange(messages);
            Updated?.Invoke();
        }

        public void Send(string author, string text)
        {
            if (string.IsNullOrWhiteSpace(text)) return;
            var msg = new ChatMessage { author = string.IsNullOrWhiteSpace(author) ? "Мастер" : author, text = text.Trim(), utcTicks = System.DateTime.UtcNow.Ticks };
            History.Add(msg);
            Updated?.Invoke();
            _ = Provider.SendAsync(msg);
        }
    }
}
