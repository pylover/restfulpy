from getpass import getpass

from restfulpy.cli.base import DatabaseLauncher


class ResetPasswordLauncher(DatabaseLauncher):
    @classmethod
    def create_parser(cls, subparsers):
        return subparsers.add_parser('reset-password', help="Create the server's database.")

    def launch(self):
        from lemur.models import Member, DBSession

        admin = Member.query.filter(Member.nickname == 'admin').one_or_none()
        if admin is None:
            raise ValueError('admin not found')
        password = getpass()
        confirm = getpass()
        if password != confirm:
            raise ValueError('Passwords not matched')
        admin.password = password
        DBSession.commit()
