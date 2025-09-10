# from django.db import models

# class ArrestRecord(models.Model):
#     apprehension_date = models.DateField(null=True, blank=True)
#     apprehension_state = models.CharField(max_length=100, null=True, blank=True)
#     apprehension_aor = models.CharField(max_length=100, null=True, blank=True)
#     apprehension_criminality = models.CharField(max_length=100, null=True, blank=True)
#     birth_year = models.IntegerField(null=True, blank=True)
#     citizenship_country = models.CharField(max_length=100, null=True, blank=True)
#     gender = models.CharField(max_length=20, null=True, blank=True)
#     unique_identifier = models.CharField(max_length=100, null=True, blank=True)
#     age = models.IntegerField(null=True, blank=True)
#     age_category = models.CharField(max_length=50, null=True, blank=True)
    
#     def __str__(self):
#         return f"{self.unique_identifier} | {self.apprehension_state} | {self.case_status}"

from django.db import models

class ArrestRecord(models.Model):
    apprehension_date = models.DateField(null=True, blank=True, db_index=True)
    apprehension_state = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    apprehension_aor = models.CharField(max_length=100, null=True, blank=True)
    apprehension_criminality = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    birth_year = models.IntegerField(null=True, blank=True)
    citizenship_country = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    gender = models.CharField(max_length=20, null=True, blank=True, db_index=True)
    unique_identifier = models.CharField(max_length=100, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    age_category = models.CharField(max_length=50, null=True, blank=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['apprehension_state', 'apprehension_date']),
            models.Index(fields=['gender', 'apprehension_date']),
            models.Index(fields=['apprehension_criminality', 'apprehension_date']),
            models.Index(fields=['citizenship_country', 'apprehension_date']),
            models.Index(fields=['age_category', 'apprehension_date']),
        ]
        ordering = ['-apprehension_date']  # default ordering for faster queries

    def __str__(self):
        return f"{self.unique_identifier} | {self.apprehension_state} | {self.apprehension_criminality}"