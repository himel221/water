from django import forms
from django.contrib.auth.models import User
from .models import Customer

class CustomerForm(forms.ModelForm):
    """Form for Customer model"""
    
    class Meta:
        model = Customer
        fields = [
            'name',
            'email',
            'phone',
            'address',
            'district',
            'is_active',
            'is_diabetic',
            'diabetes_type',
            'has_high_blood_pressure',
            'blood_pressure_status',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter customer name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter address'}),
            'district': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter district'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_diabetic': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'diabetes_type': forms.Select(attrs={'class': 'form-control'}),
            'has_high_blood_pressure': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'blood_pressure_status': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Full Name',
            'email': 'Email Address',
            'phone': 'Phone Number',
            'address': 'Address',
            'district': 'District',
            'is_active': 'Is Active?',
            'is_diabetic': 'Has Diabetes?',
            'diabetes_type': 'Diabetes Type',
            'has_high_blood_pressure': 'Has High Blood Pressure?',
            'blood_pressure_status': 'Blood Pressure Status',
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already exists (excluding current instance)
            if self.instance and self.instance.pk:
                if Customer.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError('A customer with this email already exists.')
            else:
                if Customer.objects.filter(email=email).exists():
                    raise forms.ValidationError('A customer with this email already exists.')
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove any non-digit characters
            phone = ''.join(filter(str.isdigit, phone))
            if len(phone) < 10:
                raise forms.ValidationError('Phone number must be at least 10 digits.')
        return phone


class CustomerRegistrationForm(forms.ModelForm):
    """Form for customer registration"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
        label='Password'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
        label='Confirm Password'
    )
    
    class Meta:
        model = Customer
        fields = [
            'name',
            'email',
            'phone',
            'address',
            'district',
            'is_diabetic',
            'diabetes_type',
            'has_high_blood_pressure',
            'blood_pressure_status',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your phone number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter your address'}),
            'district': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your district'}),
            'is_diabetic': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'diabetes_type': forms.Select(attrs={'class': 'form-control'}),
            'has_high_blood_pressure': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'blood_pressure_status': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already exists in Customer (case-insensitive)
            if Customer.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError('A customer with this email already exists.')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')
        
        return cleaned_data


class CustomerProfileForm(forms.ModelForm):
    """Form for customer profile update"""
    
    class Meta:
        model = Customer
        fields = [
            'name',
            'phone',
            'address',
            'district',
            'is_diabetic',
            'diabetes_type',
            'has_high_blood_pressure',
            'blood_pressure_status',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your phone number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter your address'}),
            'district': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your district'}),
            'is_diabetic': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'diabetes_type': forms.Select(attrs={'class': 'form-control'}),
            'has_high_blood_pressure': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'blood_pressure_status': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            phone = ''.join(filter(str.isdigit, phone))
            if len(phone) < 10:
                raise forms.ValidationError('Phone number must be at least 10 digits.')
        return phone