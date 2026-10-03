// إعدادات مشتركة لسكربتات k6 — كل القيم قابلة للتغيير من متغيرات البيئة
// مثال: k6 run -e BASE_URL=https://staging.mysite.ma -e VUS=20 -e DURATION=2m loadtest/k6/load.js

export const BASE_URL = __ENV.BASE_URL || "http://127.0.0.1:8000";
export const TARGET_PATH = __ENV.TARGET_PATH || "/healthz";
export const VUS = Number(__ENV.VUS || 10);
export const DURATION = __ENV.DURATION || "1m";
export const MAX_VUS = Number(__ENV.MAX_VUS || 100);

// حدود القبول: أي تجاوز يعني خروج k6 بكود خطأ (مفيد في CI)
// قابلة للضبط من البيئة: MAX_P95 / MAX_P99 / MAX_ERROR_RATE
const maxP95 = Number(__ENV.MAX_P95 || 500); // مللي ثانية
const maxP99 = Number(__ENV.MAX_P99 || 1000);
const maxErrorRate = Number(__ENV.MAX_ERROR_RATE || 0.01); // نسبة (0.01 = 1%)

export const thresholds = {
  http_req_failed: [`rate<${maxErrorRate}`],
  http_req_duration: [`p(95)<${maxP95}`, `p(99)<${maxP99}`],
  checks: ["rate>0.99"],
};

export const optionsBase = {
  thresholds,
  summaryTrendStats: ["avg", "min", "med", "p(90)", "p(95)", "p(99)", "max"],
  userAgent: "AdloabLoadTest/1.0 (authorized load test)", // نعرّف أنفسنا بوضوح
  tags: { project: "adloab-uptime" },
};
