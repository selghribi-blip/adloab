// اختبار حمل تدريجي: يرفع المستخدمين الوهميين ثم يثبّتهم ثم يهبط بهم.
// k6 run -e BASE_URL=https://staging.mysite.ma -e VUS=30 -e DURATION=2m loadtest/k6/load.js
import http from "k6/http";
import { check, sleep } from "k6";
import { BASE_URL, DURATION, VUS, TARGET_PATH, optionsBase } from "./lib/config.js";

const ramp = __ENV.RAMP || "30s";

export const options = {
  ...optionsBase,
  scenarios: {
    ramp_load: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: ramp, target: VUS },
        { duration: DURATION, target: VUS },
        { duration: ramp, target: 0 },
      ],
      gracefulRampDown: "10s",
    },
  },
};

export default function () {
  const res = http.get(`${BASE_URL}${TARGET_PATH}`, { tags: { scenario: "ramp_load" } });
  check(res, {
    "استجابة ناجحة": (r) => r.status >= 200 && r.status < 400,
    "بلا أخطاء سيرفر": (r) => r.status < 500,
  });
  sleep(Math.random() * 1.5 + 0.5); // إيقاع شبه بشري بين الطلبات
}
