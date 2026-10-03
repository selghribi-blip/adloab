// اختبار ضغط: يبحث عن «نقطة الانهيار» ويرسم منحنى الأداء حتى MAX_VUS.
// k6 run -e BASE_URL=https://staging.mysite.ma -e MAX_VUS=200 loadtest/k6/stress.js
//
// ⚠️ لا تشغّله على الإنتاج: غرضه إسقاط الخدمة عمدًا. استخدم نسخة staging.
import http from "k6/http";
import { check } from "k6";
import { BASE_URL, MAX_VUS, TARGET_PATH, optionsBase } from "./lib/config.js";

export const options = {
  ...optionsBase,
  thresholds: {
    ...optionsBase.thresholds,
    // نُبقي حدودًا لكن هدفنا هنا هو رسم المنحنى لا النجاح/الفشل
    http_req_failed: ["rate<0.05"],
  },
  scenarios: {
    stress_ramp: {
      executor: "ramping-arrival-rate",
      startRate: 10, // طلب/ثانية
      timeUnit: "1s",
      preAllocatedVUs: 20,
      maxVUs: MAX_VUS,
      stages: [
        { duration: "30s", target: 50 },
        { duration: "1m", target: 150 },
        { duration: "1m", target: 300 },
      ],
    },
  },
};

export default function () {
  const res = http.get(`${BASE_URL}${TARGET_PATH}`, { tags: { scenario: "stress_ramp" } });
  check(res, { "ردّ غير منهار": (r) => r.status < 500 });
}
