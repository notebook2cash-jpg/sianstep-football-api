# Sianstep Football JSON API

โปรเจกต์นี้ใช้สำหรับดึงข้อมูลวิเคราะห์บอลจาก `https://sianstep.com/program_football/` แล้วแปลงเป็น JSON เพื่อให้แอพเรียกใช้งานผ่าน API ได้

## สิ่งที่ทำไว้ให้แล้ว

- สคริปต์ scrape: `src/scrape.js`
- ไฟล์ JSON ล่าสุด:
  - `data/latest.json`
  - `docs/api/latest.json`
- GitHub Action: `.github/workflows/scrape-sianstep.yml`
  - รันอัตโนมัติทุกวันเวลา **11:30** และ **16:00** ตามเวลาไทย
  - (Cron ใน GitHub เป็น UTC: `30 4,9 * * *`)

## วิธีใช้งานในเครื่อง

```bash
npm install
npm run scrape
```

## ตัวอย่างโครง JSON

```json
{
  "source": "https://sianstep.com/program_football/",
  "scraped_at": "2026-03-08T14:38:24.527Z",
  "timezone": "Asia/Bangkok",
  "dates": [
    {
      "date_label": "โปรแกรมบอล วันที่ 08/03/2569",
      "leagues": [
        {
          "league_name": "บุนเดสลีกา เยอรมัน (Germany BundesLiga)",
          "matches": []
        }
      ]
    }
  ]
}
```

## วิธีเอาไปเป็น API ให้แอพเรียก

### ทางเลือกที่แนะนำ: GitHub Pages

1. ไปที่ Repository Settings -> Pages
2. เลือก Source เป็น branch `main` และโฟลเดอร์ `/docs`
3. หลังเปิดใช้งานแล้ว URL จะเป็นประมาณ:
   - `https://<username>.github.io/<repo>/api/latest.json`

### ทางเลือกเร็ว: Raw GitHub URL

- `https://raw.githubusercontent.com/<username>/<repo>/main/docs/api/latest.json`

## หมายเหตุ

- เว็บต้นทางอาจปรับโครง HTML ในอนาคต ถ้า parse ไม่ได้ให้แก้ selector ใน `src/scrape.js`
- ควรตรวจสอบเงื่อนไขการใช้งานข้อมูลของเว็บต้นทางก่อนใช้งานเชิงพาณิชย์
