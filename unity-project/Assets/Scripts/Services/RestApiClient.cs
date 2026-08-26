using System;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Networking;

namespace DreamMasters.Services
{
    /// <summary>
    /// Минимальный REST-клиент (UnityWebRequest, JSON) для Firebase Cloud Functions /
    /// Firestore REST. Никаких SDK — работает на голом Unity. TaskCompletionSource —
    /// без внешних библиотек. Таймауты обязательны: мобильный интернет рвётся.
    /// </summary>
    public class RestApiClient
    {
        private readonly string _baseUrl;
        private readonly int _timeoutSeconds;

        public RestApiClient(string baseUrl, int timeoutSeconds = 10)
        {
            _baseUrl = baseUrl.TrimEnd('/');
            _timeoutSeconds = timeoutSeconds;
        }

        public Task<ApiResponse<string>> GetAsync(string path) => SendAsync(UnityWebRequest.HttpMethod.Get, path, null);
        public Task<ApiResponse<string>> PostAsync(string path, string json) => SendAsync(UnityWebRequest.HttpMethod.Post, path, json);

        private async Task<ApiResponse<string>> SendAsync(string method, string path, string json)
        {
            string url = _baseUrl + path;
            try
            {
                using var request = new UnityWebRequest(url, method);
                request.timeout = _timeoutSeconds;
                request.downloadHandler = new DownloadHandlerBuffer();
                if (json != null)
                {
                    request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
                    request.SetRequestHeader("Content-Type", "application/json");
                }

                var tcs = new TaskCompletionSource<bool>();
                var op = request.SendWebRequest();
                op.completed += _ => tcs.TrySetResult(true);
                await tcs.Task;

#if UNITY_2020_1_OR_NEWER
                bool ok = request.result == UnityWebRequest.Result.Success;
#else
                bool ok = !request.isNetworkError && !request.isHttpError;
#endif
                if (!ok)
                    return new ApiResponse<string> { Ok = false, Error = request.error ?? "HTTP " + request.responseCode };

                return new ApiResponse<string> { Ok = true, Data = request.downloadHandler.text };
            }
            catch (Exception e)
            {
                return new ApiResponse<string> { Ok = false, Error = e.Message };
            }
        }
    }
}
