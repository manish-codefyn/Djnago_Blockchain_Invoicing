from allauth.account.adapter import DefaultAccountAdapter

class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        # Custom user save logic
        user = super().save_user(request, user, form, commit=False)
        user.save()
        return user