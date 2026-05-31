import csv
import io

from django.template import engines

from patients.models import Job

from .anonymizers import anonymize_job


class SHAReportExporter:
    def generate_monthly_csv(self, sacco_id, year, month):
        rows = Job.objects.filter(assigned_rider__sacco_id=sacco_id, status=Job.Status.DELIVERED)
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=["sha_job_code", "emergency_type", "county", "dispatch_time_seconds", "delivered_at", "anonymized_patient_id", "rider_id"], extrasaction="ignore")
        writer.writeheader()
        for job in rows:
            writer.writerow(anonymize_job(job))
        buffer.seek(0)
        return buffer

    def generate_summary_pdf(self, sacco_id, year, month):
        jobs = Job.objects.filter(assigned_rider__sacco_id=sacco_id, status=Job.Status.DELIVERED)
        template = engines["django"].from_string(
            """
            <html><body>
            <h1>SHA Summary</h1>
            <p>Total jobs: {{ total_jobs }}</p>
            <p>Average response time: {{ average_response_time }}</p>
            <p>Breakdown: {{ breakdown }}</p>
            </body></html>
            """
        )
        html = template.render({
            "total_jobs": jobs.count(),
            "average_response_time": 0,
            "breakdown": {},
        })
        try:
            from weasyprint import HTML

            return HTML(string=html).write_pdf()
        except Exception:
            return html.encode("utf-8")
