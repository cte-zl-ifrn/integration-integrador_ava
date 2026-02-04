#!/app/env/bin/python3
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    from django.core.management import execute_from_command_line

    if len(sys.argv) > 1 and sys.argv[1] in ["runserver", "runserver_plus", "test"]:
        import boot
        boot.boot()
        boot.start_debug()

    execute_from_command_line(sys.argv)
