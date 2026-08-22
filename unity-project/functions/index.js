// Dream Masters Revival — серверная часть (Firebase Cloud Functions, Node.js 20).
// Деплой: firebase deploy --only functions
// URL функций попадает в GameConfig.apiBaseUrl — клиент переключается с заглушки сам.

const functions = require("firebase-functions");
const admin = require("firebase-admin");
admin.initializeApp();
const db = admin.firestore();

const PROTOCOL_VERSION = 1;

// ---------- Профиль игрока: PUT/POST /profile?accountId=... ----------
exports.profile = functions.https.onRequest(async (req, res) => {
  cors(req, res, async () => {
    const accountId = req.query.accountId;
    if (!accountId) return res.status(400).json({ error: "accountId required" });

    if (req.method === "GET") {
      const doc = await db.collection("profiles").doc(accountId).get();
      if (!doc.exists) return res.status(404).json({ error: "not found" });
      return res.status(200).json(doc.data().payload);
    }

    if (req.method === "POST" || req.method === "PUT") {
      const payload = req.body;
      if (!payload || payload.profileVersion > PROTOCOL_VERSION + 5) {
        return res.status(400).json({ error: "bad payload" });
      }
      // Последняя запись побеждает + защита от отката времени (урок оригинала)
      await db.collection("profiles").doc(accountId).set({
        payload,
        serverUpdatedAt: admin.firestore.FieldValue.serverTimestamp(),
      }, { merge: true });
      return res.status(200).json({ ok: true });
    }

    return res.status(405).json({ error: "method not allowed" });
  });
});

// ---------- Итог боя: POST /battleResult ----------
// Античит: клиент присылает результат, сервер решает награду по своей таблице.
exports.battleResult = functions.https.onRequest(async (req, res) => {
  cors(req, res, async () => {
    if (req.method !== "POST") return res.status(405).json({ error: "POST only" });
    const { levelId, victory, secondsElapsed, protocolVersion } = req.body || {};
    if (!levelId) return res.status(400).json({ error: "levelId required" });

    // Таблица наград сервера (перенести сюда значения LevelData при деплое)
    const rewardTable = {
      default: { gold: 200, shard: 10, rune: 6 },
    };
    const base = rewardTable[levelId] || rewardTable.default;

    // Грубая античит-эвристика: бой не мог длиться меньше 5 секунд
    const sane = victory ? Number(secondsElapsed) >= 5 : true;
    const rewards = sane && victory ? base : { gold: Math.floor(base.gold / 4), shard: 2, rune: 1 };

    // TODO(итерация 4): писать в историю боёв, обновлять рейтинг арены.
    return res.status(200).json(rewards);
  });
});

// ---------- Арена: GET /arenaOpponents?rating=... ----------
exports.arenaOpponents = functions.https.onRequest(async (req, res) => {
  cors(req, res, async () => {
    const rating = Number(req.query.rating) || 1000;
    const snap = await db.collection("arena")
      .where("rating", ">=", rating - 100)
      .where("rating", "<=", rating + 100)
      .limit(10)
      .get();
    const opponents = snap.docs.map((d) => d.data());
    return res.status(200).json(opponents);
  });
});

// ---------- Чат: GET /chat (последние 50), POST /chat ----------
exports.chat = functions.https.onRequest(async (req, res) => {
  cors(req, res, async () => {
    if (req.method === "GET") {
      const snap = await db.collection("chat")
        .orderBy("utcTicks", "desc").limit(50).get();
      return res.status(200).json(snap.docs.map((d) => d.data()).reverse());
    }
    if (req.method === "POST") {
      const { author, text } = req.body || {};
      if (!author || !text) return res.status(400).json({ error: "author and text required" });
      if (String(text).length > 300) return res.status(400).json({ error: "too long" });
      await db.collection("chat").add({
        author: String(author).slice(0, 40),
        text: String(text).slice(0, 300),
        utcTicks: Date.now(),
      });
      return res.status(200).json({ ok: true });
    }
    return res.status(405).json({ error: "method not allowed" });
  });
});

function cors(req, res, handler) {
  res.set("Access-Control-Allow-Origin", "*");
  res.set("Access-Control-Allow-Methods", "GET,POST,PUT,OPTIONS");
  res.set("Access-Control-Allow-Headers", "Content-Type");
  if (req.method === "OPTIONS") return res.status(204).end();
  return handler();
}
