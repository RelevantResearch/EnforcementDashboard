from django.db import models

class ArrestRecord(models.Model):
    apprehension_date = models.DateField(null=True, blank=True)
    apprehension_state = models.CharField(max_length=100, null=True, blank=True)
    apprehension_aor = models.CharField(max_length=100, null=True, blank=True)
    final_program = models.CharField(max_length=100, null=True, blank=True)
    final_program_group = models.CharField(max_length=100, null=True, blank=True)
    apprehension_method = models.CharField(max_length=100, null=True, blank=True)
    apprehension_criminality = models.CharField(max_length=100, null=True, blank=True)
    case_status = models.CharField(max_length=100, null=True, blank=True)
    case_category = models.CharField(max_length=100, null=True, blank=True)
    departed_date = models.DateField(null=True, blank=True)
    departure_country = models.CharField(max_length=100, null=True, blank=True)
    final_order_yes_no = models.CharField(max_length=10, null=True, blank=True)
    final_order_date = models.DateField(null=True, blank=True)
    birth_year = models.IntegerField(null=True, blank=True)
    citizenship_country = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    apprehension_site_landmark = models.CharField(max_length=200, null=True, blank=True)
    unique_identifier = models.CharField(max_length=100, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    age_category = models.CharField(max_length=50, null=True, blank=True)
    
    def __str__(self):
        return f"{self.unique_identifier} | {self.apprehension_state} | {self.case_status}"