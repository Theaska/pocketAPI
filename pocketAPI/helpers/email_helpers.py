from django.template.loader import get_template


def create_email_template(template_name, context=None):
    """
        Create email message using template.
    """
    if context is None:
        context = {}
    template = get_template(template_name)
    message = template.render(context)
    return message
