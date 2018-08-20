<%
    url = '%s?t_=%s' % (reset_password_callback_url, reset_password_token)
%>

<html>
    <head>
        <meta name="viewport" content="width=device-width"/>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
    </head>

    <body>
    	<h1>Carrene Authentication Service</h1>
        <p> Click <a href="${url}">here</a> to continue reset password.</p>
    </body>
</html>
