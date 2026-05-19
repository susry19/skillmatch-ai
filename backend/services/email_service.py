"""
E-posta servisi — FastAPI-Mail ile SMTP/SendGrid entegrasyonu.
Tüm transaksiyonel e-postalar buradan gönderilir:
  - Mülakat daveti
  - Teklif bildirimi
  - Başvuru durum güncellemesi
  - Aday portal erişim linki
  - Onboarding karşılama
"""
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pathlib import Path
from typing import Optional, List
import logging
from config import settings

logger = logging.getLogger(__name__)

# FastAPI-Mail yapılandırması
mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

fast_mail = FastMail(mail_config)


# ─── TEMEL GÖNDERIM FONKSİYONU ────────────────────────────────────────────────

async def send_email(
    recipients: List[str],
    subject: str,
    html_body: str,
) -> bool:
    """Temel HTML e-posta gönderim fonksiyonu."""
    try:
        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            body=html_body,
            subtype=MessageType.html,
        )
        await fast_mail.send_message(message)
        logger.info(f"E-posta gönderildi: {recipients} — {subject}")
        return True
    except Exception as e:
        logger.error(f"E-posta gönderim hatası: {e}")
        return False


# ─── HTML ŞABLONLAR ───────────────────────────────────────────────────────────

def _base_template(content: str, title: str) -> str:
    """Tüm e-postalar için temel HTML şablonu."""
    return f"""
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
</head>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;padding:40px 20px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#6366f1,#4f46e5);padding:32px 40px;">
            <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:600;letter-spacing:-0.3px;">
              SkillMatch AI
            </h1>
            <p style="margin:4px 0 0;color:rgba(255,255,255,0.75);font-size:13px;">
              Akıllı İşe Alım Platformu
            </p>
          </td>
        </tr>

        <!-- Content -->
        <tr>
          <td style="padding:36px 40px;">
            {content}
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#f8f9fc;padding:20px 40px;border-top:1px solid #eef0f5;">
            <p style="margin:0;color:#9ca3af;font-size:12px;text-align:center;">
              Bu e-posta SkillMatch AI tarafından otomatik olarak gönderilmiştir.<br>
              Soru ve görüşleriniz için <a href="mailto:{settings.MAIL_FROM}" style="color:#6366f1;">iletişime geçin</a>.
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>
"""


# ─── TRANSAKSIYONEL E-POSTALAR ────────────────────────────────────────────────

async def send_interview_invitation(
    candidate_email: str,
    candidate_name: str,
    position_title: str,
    interview_type: str,
    scheduled_at: str,
    duration_minutes: int,
    location_or_link: str,
    interviewer_name: str,
    portal_link: Optional[str] = None,
) -> bool:
    """Adaya mülakat daveti gönderir."""

    portal_section = ""
    if portal_link:
        portal_section = f"""
        <div style="background:#f0f4ff;border-radius:8px;padding:16px;margin:20px 0;">
          <p style="margin:0 0 8px;font-size:13px;color:#6366f1;font-weight:600;">Başvuru Takip Portalı</p>
          <p style="margin:0 0 12px;font-size:13px;color:#6b7280;">Başvurunuzun durumunu takip etmek için:</p>
          <a href="{portal_link}" style="background:#6366f1;color:#ffffff;padding:10px 20px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:500;">Portala Git</a>
        </div>
        """

    type_labels = {
        "phone": "Telefon Görüşmesi",
        "video": "Video Konferans",
        "onsite": "Yüz Yüze Görüşme",
        "technical": "Teknik Mülakat",
        "hr": "İK Mülakatı",
    }
    type_label = type_labels.get(interview_type, interview_type)

    content = f"""
    <h2 style="margin:0 0 8px;color:#1f2937;font-size:20px;">Mülakat Davetiniz Hazır!</h2>
    <p style="color:#6b7280;font-size:14px;margin:0 0 24px;">Sayın {candidate_name},</p>

    <p style="color:#374151;font-size:14px;line-height:1.6;margin:0 0 20px;">
      <strong>{position_title}</strong> pozisyonu için başvurunuz değerlendirilmiş ve
      sizi mülakate davet etmekten memnuniyet duyuyoruz.
    </p>

    <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:20px;margin:0 0 20px;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr><td style="padding:6px 0;">
          <span style="color:#9ca3af;font-size:12px;display:block;">Mülakat Türü</span>
          <span style="color:#1f2937;font-size:14px;font-weight:500;">{type_label}</span>
        </td></tr>
        <tr><td style="padding:6px 0;">
          <span style="color:#9ca3af;font-size:12px;display:block;">Tarih ve Saat</span>
          <span style="color:#1f2937;font-size:14px;font-weight:500;">{scheduled_at}</span>
        </td></tr>
        <tr><td style="padding:6px 0;">
          <span style="color:#9ca3af;font-size:12px;display:block;">Süre</span>
          <span style="color:#1f2937;font-size:14px;font-weight:500;">{duration_minutes} dakika</span>
        </td></tr>
        <tr><td style="padding:6px 0;">
          <span style="color:#9ca3af;font-size:12px;display:block;">Yer / Link</span>
          <span style="color:#1f2937;font-size:14px;font-weight:500;">{location_or_link}</span>
        </td></tr>
        <tr><td style="padding:6px 0;">
          <span style="color:#9ca3af;font-size:12px;display:block;">Görüşmeci</span>
          <span style="color:#1f2937;font-size:14px;font-weight:500;">{interviewer_name}</span>
        </td></tr>
      </table>
    </div>

    {portal_section}

    <p style="color:#6b7280;font-size:13px;line-height:1.6;margin:20px 0 0;">
      Herhangi bir sorunuz olursa lütfen bizimle iletişime geçmekten çekinmeyin.
      Görüşmemizde başarılar dileriz!
    </p>
    """

    return await send_email(
        recipients=[candidate_email],
        subject=f"Mülakat Daveti — {position_title}",
        html_body=_base_template(content, "Mülakat Daveti"),
    )


async def send_offer_notification(
    candidate_email: str,
    candidate_name: str,
    position_title: str,
    proposed_salary: int,
    currency: str,
    start_date: str,
    benefits: List[str],
    portal_link: Optional[str] = None,
    expires_at: Optional[str] = None,
) -> bool:
    """Adaya iş teklifi bildirimini gönderir."""

    benefits_html = ""
    if benefits:
        items = "".join(f'<li style="color:#374151;font-size:13px;padding:2px 0;">{b}</li>' for b in benefits)
        benefits_html = f"""
        <div style="margin:16px 0;">
          <p style="color:#374151;font-size:13px;font-weight:600;margin:0 0 8px;">Sağlanan Yan Haklar:</p>
          <ul style="margin:0;padding-left:20px;">{items}</ul>
        </div>
        """

    portal_section = ""
    if portal_link:
        portal_section = f"""
        <div style="text-align:center;margin:24px 0;">
          <a href="{portal_link}" style="background:#6366f1;color:#ffffff;padding:14px 32px;border-radius:8px;text-decoration:none;font-size:14px;font-weight:600;display:inline-block;">
            Teklifi İncele ve Yanıtla
          </a>
        </div>
        """

    expiry_section = f'<p style="color:#ef4444;font-size:13px;margin:12px 0 0;">Teklifin son geçerlilik tarihi: <strong>{expires_at}</strong></p>' if expires_at else ""

    content = f"""
    <h2 style="margin:0 0 8px;color:#1f2937;font-size:20px;">İş Teklifi Aldınız!</h2>
    <p style="color:#6b7280;font-size:14px;margin:0 0 24px;">Sayın {candidate_name},</p>

    <p style="color:#374151;font-size:14px;line-height:1.6;margin:0 0 20px;">
      <strong>{position_title}</strong> pozisyonu için değerlendirme süreciniz tamamlanmış olup
      size bir iş teklifi sunmaktan büyük memnuniyet duyuyoruz.
    </p>

    <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:20px;margin:0 0 20px;">
      <p style="margin:0 0 4px;font-size:12px;color:#16a34a;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Önerilen Maaş</p>
      <p style="margin:0;font-size:28px;font-weight:700;color:#15803d;">
        {proposed_salary:,} {currency}
        <span style="font-size:14px;font-weight:400;color:#16a34a;">/ aylık net</span>
      </p>
    </div>

    <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:20px;margin:0 0 16px;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr><td style="padding:4px 0;">
          <span style="color:#9ca3af;font-size:12px;">Başlangıç Tarihi</span><br>
          <span style="color:#1f2937;font-size:14px;font-weight:500;">{start_date}</span>
        </td></tr>
      </table>
    </div>

    {benefits_html}
    {portal_section}
    {expiry_section}

    <p style="color:#6b7280;font-size:13px;line-height:1.6;margin:20px 0 0;">
      Herhangi bir sorunuz varsa veya müzakere etmek isterseniz bizimle iletişime geçebilirsiniz.
    </p>
    """

    return await send_email(
        recipients=[candidate_email],
        subject=f"İş Teklifi — {position_title}",
        html_body=_base_template(content, "İş Teklifi"),
    )


async def send_status_update(
    candidate_email: str,
    candidate_name: str,
    position_title: str,
    new_status: str,
    message: Optional[str] = None,
    portal_link: Optional[str] = None,
) -> bool:
    """Başvuru durum değişikliği bildirimi gönderir."""

    status_labels = {
        "applied": ("Başvurunuz Alındı", "#6366f1", "Başvurunuz sistemimize başarıyla kaydedildi."),
        "screening": ("Başvurunuz İnceleniyor", "#f59e0b", "CV'niz İK ekibimiz tarafından inceleniyor."),
        "interview_scheduled": ("Mülakat Planlandı", "#3b82f6", "Mülakat planlamanız tamamlandı."),
        "interview_done": ("Mülakat Tamamlandı", "#8b5cf6", "Mülakat süreciniz tamamlandı, değerlendirme yapılıyor."),
        "offer_sent": ("Teklif Gönderildi", "#10b981", "Size bir iş teklifi gönderildi."),
        "offer_accepted": ("Teklif Kabul Edildi", "#10b981", "Teklifinizi kabul ettiğiniz için teşekkürler!"),
        "hired": ("İşe Alındınız!", "#10b981", "Aramıza hoş geldiniz!"),
        "rejected": ("Başvurunuz Hakkında Güncelleme", "#6b7280", "Başvurunuz değerlendirilmiş olup bu pozisyon için süreciniz tamamlanmıştır."),
    }

    label, color, default_msg = status_labels.get(new_status, ("Durum Güncellendi", "#6366f1", "Başvurunuzda bir güncelleme var."))
    display_message = message or default_msg

    portal_section = ""
    if portal_link:
        portal_section = f"""
        <div style="text-align:center;margin:20px 0;">
          <a href="{portal_link}" style="background:{color};color:#ffffff;padding:12px 28px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:500;display:inline-block;">
            Başvurumu Takip Et
          </a>
        </div>
        """

    content = f"""
    <div style="display:inline-block;background:{color}1a;color:{color};padding:6px 14px;border-radius:20px;font-size:12px;font-weight:600;margin-bottom:16px;">
      {label}
    </div>

    <h2 style="margin:0 0 16px;color:#1f2937;font-size:18px;">{position_title} Başvurusu</h2>
    <p style="color:#6b7280;font-size:14px;margin:0 0 16px;">Sayın {candidate_name},</p>

    <p style="color:#374151;font-size:14px;line-height:1.6;margin:0 0 20px;">
      {display_message}
    </p>

    {portal_section}
    """

    return await send_email(
        recipients=[candidate_email],
        subject=f"{label} — {position_title}",
        html_body=_base_template(content, label),
    )


async def send_portal_access_link(
    candidate_email: str,
    candidate_name: str,
    portal_link: str,
) -> bool:
    """Adaya portal erişim linkini gönderir."""

    content = f"""
    <h2 style="margin:0 0 16px;color:#1f2937;font-size:20px;">Başvuru Takip Portalı</h2>
    <p style="color:#6b7280;font-size:14px;margin:0 0 16px;">Sayın {candidate_name},</p>

    <p style="color:#374151;font-size:14px;line-height:1.6;margin:0 0 24px;">
      SkillMatch AI başvuru takip portalınıza erişim linkiniz aşağıda yer almaktadır.
      Bu link aracılığıyla başvurularınızın durumunu, mülakat davetlerinizi ve tekliflerinizi
      gerçek zamanlı takip edebilirsiniz.
    </p>

    <div style="background:#f0f4ff;border-radius:8px;padding:20px;margin:0 0 20px;text-align:center;">
      <p style="margin:0 0 12px;font-size:13px;color:#6b7280;">Kişisel erişim linkiniz:</p>
      <a href="{portal_link}" style="background:#6366f1;color:#ffffff;padding:14px 32px;border-radius:8px;text-decoration:none;font-size:14px;font-weight:600;display:inline-block;">
        Portala Git
      </a>
      <p style="margin:12px 0 0;font-size:11px;color:#9ca3af;">
        Bu link yalnızca size özeldir. Başkalarıyla paylaşmayınız.
      </p>
    </div>
    """

    return await send_email(
        recipients=[candidate_email],
        subject="SkillMatch AI — Başvuru Takip Portalınız",
        html_body=_base_template(content, "Portal Erişimi"),
    )


async def send_onboarding_welcome(
    candidate_email: str,
    candidate_name: str,
    position_title: str,
    start_date: str,
    manager_name: str,
    tasks: List[dict],
    portal_link: Optional[str] = None,
) -> bool:
    """İşe alınan adaya onboarding karşılama e-postası gönderir."""

    tasks_html = ""
    if tasks:
        rows = ""
        for task in tasks[:8]:  # İlk 8 görevi göster
            rows += f"""
            <tr>
              <td style="padding:8px;border-bottom:1px solid #f3f4f6;font-size:13px;color:#374151;">{task.get('title', '')}</td>
              <td style="padding:8px;border-bottom:1px solid #f3f4f6;font-size:12px;color:#9ca3af;">{task.get('category', '')}</td>
              <td style="padding:8px;border-bottom:1px solid #f3f4f6;font-size:12px;color:#6366f1;">Gün {task.get('due_days_after_start', 1)}</td>
            </tr>
            """
        tasks_html = f"""
        <div style="margin:20px 0;">
          <p style="color:#374151;font-size:13px;font-weight:600;margin:0 0 8px;">Onboarding Checklist:</p>
          <table width="100%" style="border-collapse:collapse;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">
            <tr style="background:#f9fafb;">
              <th style="padding:8px;text-align:left;font-size:12px;color:#6b7280;">Görev</th>
              <th style="padding:8px;text-align:left;font-size:12px;color:#6b7280;">Kategori</th>
              <th style="padding:8px;text-align:left;font-size:12px;color:#6b7280;">Süre</th>
            </tr>
            {rows}
          </table>
        </div>
        """

    portal_section = ""
    if portal_link:
        portal_section = f"""
        <div style="text-align:center;margin:24px 0;">
          <a href="{portal_link}" style="background:#6366f1;color:#ffffff;padding:14px 32px;border-radius:8px;text-decoration:none;font-size:14px;font-weight:600;display:inline-block;">
            Onboarding Portalıma Git
          </a>
        </div>
        """

    content = f"""
    <h2 style="margin:0 0 8px;color:#1f2937;font-size:22px;">Aramıza Hoş Geldiniz!</h2>
    <p style="color:#6b7280;font-size:14px;margin:0 0 24px;">Sayın {candidate_name},</p>

    <p style="color:#374151;font-size:14px;line-height:1.6;margin:0 0 16px;">
      <strong>{position_title}</strong> pozisyonu için işe alım süreciniz tamamlandı.
      Sizi ekibimizde görmekten heyecan duyuyoruz!
    </p>

    <div style="background:#f0fdf4;border-left:4px solid #10b981;padding:16px;border-radius:0 8px 8px 0;margin:0 0 20px;">
      <p style="margin:0 0 4px;font-size:12px;color:#16a34a;font-weight:600;">Başlangıç Tarihiniz</p>
      <p style="margin:0;font-size:18px;font-weight:700;color:#15803d;">{start_date}</p>
    </div>

    <p style="color:#374151;font-size:14px;margin:0 0 4px;">
      <strong>Yöneticiniz:</strong> {manager_name}
    </p>

    {tasks_html}
    {portal_section}

    <p style="color:#6b7280;font-size:13px;line-height:1.6;margin:20px 0 0;">
      Herhangi bir sorunuz olursa İK ekibimizle iletişime geçebilirsiniz. Başarılar!
    </p>
    """

    return await send_email(
        recipients=[candidate_email],
        subject=f"Hoş Geldiniz — {position_title} Onboarding",
        html_body=_base_template(content, "Hoş Geldiniz"),
    )
