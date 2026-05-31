from django.db import models

from core.models import TimeStampedModel


class SHAReimbursementRecord(TimeStampedModel):
    """
    Tracks billing transactions submitted directly to the Social Health Authority.
    Must exist in the initial database migration tree.
    """

    job = models.OneToOneField("patients.Job", on_delete=models.CASCADE)
    sacco = models.ForeignKey("saccos.Sacco", on_delete=models.CASCADE)
    triage_category = models.CharField(max_length=20)
    processed_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "reports_sha_reimbursement"