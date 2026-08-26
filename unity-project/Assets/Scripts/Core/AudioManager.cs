using System.Collections.Generic;
using UnityEngine;
using DreamMasters.Progress;

namespace DreamMasters.Core
{
    /// <summary>Идентификаторы звуковых эффектов (файлы в Resources/Audio).</summary>
    public enum Sfx
    {
        Click, Hit, Crit, Cast, Heal, Victory, Defeat, BossRoar
    }

    /// <summary>
    /// Звук: музыкальный луп + пул источников для SFX. Громкости из профиля,
    /// пауза при сворачивании приложения (жизненный цикл Android).
    /// Клипы лежат в Resources/Audio — сгенерированы tools/generate_audio.py.
    /// </summary>
    public class AudioManager : MonoBehaviour
    {
        public static AudioManager Instance { get; private set; }

        [SerializeField] private int sfxSources = 6;
        [SerializeField] private string audioFolder = "Audio";

        private AudioSource _music;
        private readonly List<AudioSource> _sfxPool = new List<AudioSource>();
        private readonly Dictionary<Sfx, AudioClip> _clips = new Dictionary<Sfx, AudioClip>();
        private int _nextSource;

        private void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);

            _music = gameObject.AddComponent<AudioSource>();
            _music.loop = true;
            _music.playOnAwake = false;

            for (int i = 0; i < sfxSources; i++)
            {
                var src = gameObject.AddComponent<AudioSource>();
                src.playOnAwake = false;
                _sfxPool.Add(src);
            }

            LoadClips();
        }

        private void Start()
        {
            var gm = GameManager.Instance;
            if (gm != null)
            {
                ApplyVolumes(gm.Profile);
                gm.ProfileChanged += ApplyVolumes;
            }
            PlayMusic();
        }

        private void OnDestroy()
        {
            var gm = GameManager.Instance;
            if (gm != null) gm.ProfileChanged -= ApplyVolumes;
            if (Instance == this) Instance = null;
        }

        private void LoadClips()
        {
            foreach (Sfx id in System.Enum.GetValues(typeof(Sfx)))
            {
                var clip = Resources.Load<AudioClip>(audioFolder + "/" + id);
                if (clip != null) _clips[id] = clip;
            }
            var music = Resources.Load<AudioClip>(audioFolder + "/music_dream");
            if (music != null) _music.clip = music;
        }

        public void PlayMusic()
        {
            if (_music.clip != null && !_music.isPlaying) _music.Play();
        }

        public void Play(Sfx id, float volumeScale = 1f)
        {
            if (!_clips.TryGetValue(id, out var clip)) return;
            var src = _sfxPool[_nextSource];
            _nextSource = (_nextSource + 1) % _sfxPool.Count;
            src.PlayOneShot(clip, volumeScale);
        }

        public void ApplyVolumes(PlayerProfile profile)
        {
            if (profile == null) return;
            _music.volume = profile.musicVolume;
            foreach (var s in _sfxPool) s.volume = profile.sfxVolume;
        }

        /// <summary>Пауза при сворачивании (вызывается GameManager).</summary>
        public void SetSuspended(bool suspended)
        {
            if (suspended) _music.Pause(); else _music.UnPause();
        }
    }
}
