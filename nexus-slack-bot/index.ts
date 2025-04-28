import { config } from "dotenv";
import { App } from "@slack/bolt";

config();

const SLACK_BOT_TOKEN = process.env.SLACK_BOT_TOKEN;
const SLACK_SIGNING_SECRET = process.env.SLACK_SIGNING_SECRET;
const TARGET_CHANNEL_ID = process.env.TARGET_CHANNEL_ID;

if (!SLACK_BOT_TOKEN || !SLACK_SIGNING_SECRET || !TARGET_CHANNEL_ID) {
  throw new Error(
    "Missing required environment variables: SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, and/or TARGET_CHANNEL_ID"
  );
}

console.log("Bot token exists:", !!SLACK_BOT_TOKEN);
console.log("Signing secret exists:", !!SLACK_SIGNING_SECRET);
console.log("Target channel ID:", TARGET_CHANNEL_ID);

const app = new App({
  token: SLACK_BOT_TOKEN,
  signingSecret: SLACK_SIGNING_SECRET,
});

async function sendHelloMessage() {
  try {
    const result = await app.client.chat.postMessage({
      channel: TARGET_CHANNEL_ID as string,
      text: "Hello! 👋",
    });
    console.log("✅ Message sent successfully:", result);
  } catch (error) {
    console.error("❌ Error sending message:", error);
  }
}

(async () => {
  try {
    setInterval(sendHelloMessage, 60000);

    console.log("⚡️ Bot is running and will send messages every minute!");
  } catch (error) {
    console.error("Error starting bot:", error);
  }
})();
