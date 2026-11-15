# Источники и границы / Sources and scope

1. Последние переданные владельцем метаданные рабочего backend: Python 3.12.15, PostgreSQL 16.15, схема `0035_editorial`. Это исторические сведения из переписки, не свежий опрос VDS.
2. Исходники и отчёты ранее подготовленного ТЗ №30: `vmeste-solo61/backend/app/main.py`, `routers/requests.py`, `subscriptions.py`, `routers/subscriptions.py`, `website/src/admin/BannerConstructor.tsx`, `admin/ControlCenter.tsx`, `lib/browserSpeech.ts`, `lib/speechReplies.ts`, `features/VoiceAssistant.tsx`, материалы `integrations/vesta29` и `integrations/vesta30`. Они показывают реализацию и ограничения рассмотренного кандидата, а не весь текущий production. Репозиторий: https://github.com/isidisis49-ctrl/111
3. Каталог №33: 81 запись, 56 draft / 25 hold; отчёт лаборатории №33 и результат владельца по AutoTest Catalog33 Fix3, 14 ноября 2026: 158 pytest PASS / 7 SKIP; с окружением 160 PASS / 0 FAIL / 7 SKIP. Не заменяет приёмку VDS.
4. Иллюстрации и реальные локальные снимки интерфейсов взяты из собственной книжной ветки, immutable commit `993c830e8ceb589d07599f6045fe316cd7adcd6b`. Снимки иностранного интерфейса редакционно локализованы; микрофон и настоящая модель при их создании не испытывались. Исходные пути и SHA-256 — `asset-sources.json`.
5. Браузерный голос: https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition и https://webkit.org/blog/11648/new-webkit-features-in-safari-14-1/ . Это документация API, не результат испытания нашего приложения.
6. Самостоятельный Android: https://developer.android.com/reference/android/speech/SpeechRecognizer и https://developer.android.com/reference/android/speech/RecognizerIntent . Доступность on-device распознавания и языка проверяется во время работы; предпочтение offline не гарантирует автономность.
7. Следующее iOS-направление: https://developer.apple.com/documentation/Speech/SFSpeechRecognizer/supportsOnDeviceRecognition . Поддержка зависит от языка и устройства; приложение ещё предстоит разработать.
8. Денежные оценки — собственная сценарная модель трудозатрат и условных ставок, а не проверенные рыночные котировки. Методика и исключения указаны в паспорте и `cost-model.json`.

## Что не использовалось и не выполнялось

Никакие секреты, персональные записи пользователей, приватные конфигурации, дампы или внутренние документы предприятий не публикуются. Названия заводов и заказчиков не приводятся. Пользовательская промышленная презентация не включена в комплект. VDS не опрашивался, production-запросы и операции изменения не выполнялись. Ни одна схема паспорта не выдаётся за автоматически обнаруженную инфраструктуру.

No secrets, private records, enterprise identities or internal presentation assets are included. The passport does not certify live deployment, mobile applications, speech hardware, statutory compliance, capacity or a sale value. Official API documentation informs the design but is not a test of our software.
