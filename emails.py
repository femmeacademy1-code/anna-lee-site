"""The texts of the emails for the free lecture "על קוצים".

DRAFTS for Anna Lee's approval. To change a text, edit it here; nothing else needs to change.
Placeholders: {name} (first name), {when} (day and date), {time}, {zoom} (the Zoom link),
{kit} (link to the regulation kit), {site} (the site's address).
"""

LECTURE_TITLE = "על קוצים: למה הגוף שלך כל הזמן בכוננות ואיך מפסיקים לפחד מהחרדה"

# 1. right after registering
CONFIRM = {
    "subject": "נרשמת להרצאה \"על קוצים\" | {when} ב-{time}",
    "body": """<p>היי {name},</p>
<p>איזה כיף שנרשמת להרצאה <strong>"{title}"</strong>.</p>
<p><strong>מתי:</strong> {when}, בשעה {time}<br>
<strong>איפה:</strong> בזום, בלייב<br>
<strong>משך:</strong> 30 דקות</p>
{zoom_block}
<p>ההרצאה לא תוקלט, אז כדאי לשריין את הזמן ביומן.<br>
יום לפני ההרצאה, ושוב שעה לפני, אשלח לך תזכורת עם הקישור.</p>
<p>מחכה לראות אותך,<br>אנה לי</p>""",
}

# 2. the day before, at the same hour
REMINDER_DAY = {
    "subject": "מחר ב-{time}: ההרצאה \"על קוצים\"",
    "body": """<p>היי {name},</p>
<p>רק תזכורת קטנה: <strong>מחר, {when}, בשעה {time}</strong> נפגשות בזום להרצאה "על קוצים".</p>
{zoom_block}
<p>30 דקות של הבנה, תרגול וכלים ראשוניים. ההרצאה לא תוקלט, אז כדאי לשריין את הזמן.</p>
<p>נתראה מחר,<br>אנה לי</p>""",
}

# 3. one hour before
REMINDER_HOUR = {
    "subject": "עוד שעה מתחילות: \"על קוצים\"",
    "body": """<p>היי {name},</p>
<p>בעוד שעה, <strong>ב-{time}</strong>, אנחנו מתחילות.</p>
{zoom_block}
<p>כדאי למצוא מקום שקט ונוח לחצי שעה. אם אפשר, להתחבר כמה דקות לפני.</p>
<p>נתראה עוד מעט,<br>אנה לי</p>""",
}

# 4. after the lecture: the regulation kit and the workshop offer.
# Not sent until config.json -> lecture -> after_email_ready is true (it waits for the offer details).
AFTER = {
    "subject": "תודה שהיית איתי, והמתנה שהבטחתי",
    "body": """<p>היי {name},</p>
<p>תודה שהקדשת לעצמך את הזמן הזה הערב.</p>
<p>כמו שהבטחתי, הנה <strong>ערכת הוויסות: עזרה ראשונה לרגעי הצפה</strong>.<br>
כדאי לשמור אותה כצילום מסך בטלפון, כדי שתהיה איתך ברגעים שבהם קשה לחשוב בבהירות.</p>
<p><a class="btn" href="{kit}">לערכת הוויסות</a></p>
{offer_block}
<p>באהבה,<br>אנה לי</p>""",
}

ZOOM_BLOCK = '<p><a class="btn" href="{zoom}">לכניסה לזום</a></p>'
ZOOM_LATER = "<p>את הקישור לזום אשלח אלייך במייל התזכורת.</p>"

# to Anna Lee, for every new lead
NOTIFY = {
    "subject": "פנייה חדשה מהאתר: {name} ({topic})",
    "body": """<p><strong>{name}</strong> השאירה פרטים באתר.</p>
<p><strong>נושא:</strong> {topic}<br>
<strong>מייל:</strong> {email}<br>
<strong>טלפון:</strong> {phone}<br>
<strong>הסכמה לדיוור:</strong> {consent}</p>
{message_block}
<p>כל הפניות בממשק הניהול: {site}/admin</p>""",
}

FOOTER = ("קיבלת את המייל הזה כי נרשמת להרצאה באתר של אנה לי מילשטיין. "
          "אם זו טעות, אפשר פשוט להשיב למייל.")
