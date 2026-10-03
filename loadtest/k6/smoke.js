// فحص دخاني: طلب واحد للتأكد أن السيناريو سليم قبل أي اختبار حمل حقيقي.
// k6 run -e BASE_URL=https://staging.mysite.ma loadtest/k6/smoke.js
import http from "k6/http";
import { check, sleep } from "k6";
import { BASE_URL, TARGET_PATH, optionsBase } from "./lib/config.js";

export const options = {
  ...optionsBase,
  vus: 1,
  iterations: 5,
};

export default function () {
  const res = http.get(`${BASE_URL}${TARGET_PATH}`);
  check(res, {
    "رمز الحالة 200": (r) => r.status === 200,
    "زمن الاستجابة < 800ms": (r) => r.timings.duration < 800,
  });
  sleep(1);
}
