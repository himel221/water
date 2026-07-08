from django import forms
from .models import Customer

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'name', 'email', 'phone', 'address', 
            'city', 'state', 'pincode', 
            'company_name', 'gst_number',
            # Health fields
            'has_diabetes', 'diabetes_notes',
            'blood_pressure', 'blood_pressure_notes',
            'other_health_conditions'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full name',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number',
                'required': True
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter address',
                'required': True
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter city',
                'required': True
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter state',
                'required': True
            }),
            'pincode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter pincode',
                'required': True
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Company name (optional)'
            }),
            'gst_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'GST number (optional)'
            }),
            'has_diabetes': forms.Select(attrs={
                'class': 'form-select',
            }),
            'diabetes_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'e.g., Type 2 Diabetes, taking Metformin'
            }),
            'blood_pressure': forms.Select(attrs={
                'class': 'form-select',
            }),
            'blood_pressure_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'e.g., Taking Lisinopril 10mg daily'
            }),
            'other_health_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Any other health conditions or allergies'
            }),
        }
        labels = {
            'name': 'Full Name',
            'email': 'Email Address',
            'phone': 'Phone Number',
            'address': 'Delivery Address',
            'city': 'City',
            'state': 'State/Province',
            'pincode': 'Pincode',
            'company_name': 'Company Name (Optional)',
            'gst_number': 'GST Number (Optional)',
            'has_diabetes': 'Diabetes Status',
            'diabetes_notes': 'Diabetes Notes (Optional)',
            'blood_pressure': 'Blood Pressure Status',
            'blood_pressure_notes': 'Blood Pressure Notes (Optional)',
            'other_health_conditions': 'Other Health Conditions (Optional)',
        }
        help_texts = {
            'diabetes_notes': 'Please provide details about diabetes type, medications, or management',
            'blood_pressure_notes': 'Please provide details about blood pressure readings or medications',
            'other_health_conditions': 'Any allergies, chronic conditions, or other health concerns',
        }
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Remove any spaces or special characters
        phone = ''.join(filter(str.isdigit, phone))
        if len(phone) < 10:
            raise forms.ValidationError("Phone number must be at least 10 digits")
        if len(phone) > 15:
            raise forms.ValidationError("Phone number must be less than 15 digits")
        return phone
    
    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        pincode = ''.join(filter(str.isdigit, pincode))
        if len(pincode) not in [5, 6]:
            raise forms.ValidationError("Pincode must be 5 or 6 digits")
        return pincode
    
    def clean(self):
        cleaned_data = super().clean()
        has_diabetes = cleaned_data.get('has_diabetes')
        diabetes_notes = cleaned_data.get('diabetes_notes')
        
        # If customer has diabetes, recommend they provide notes
        if has_diabetes in ['yes', 'pre', 'gestational'] and not diabetes_notes:
            self.add_error('diabetes_notes', 'Please provide details about your diabetes condition')
        
        return cleaned_data