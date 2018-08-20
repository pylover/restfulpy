<%
    url = '%s?t_=%s' % (registeration_callback_url, registeration_token)
%>

<html>
    <head>
        <meta name="viewport" content="width=device-width"/>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
    </head>

    <body>
    	<h1>Carrene Authentication Service</h1>
        <p> Click <a href="${url}">here</a> to continue registration.</p>
    </body>
</html>
