<!doctype html>
<html>
	<head>
		<meta charset="utf-8">
		<meta http-equiv="X-UA-Compatible" content="IE=edge">
		<meta name="viewport" content="width=device-width, initial-scale=1">
		<title>Interest Link - ${heading}</title>
		<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.1/css/bootstrap.min.css">
		<link rel="stylesheet" href="/static/style.css">
		<link rel="icon" type="image/x-icon" href="/static/favicon.ico">
		<script src="https://code.jquery.com/jquery-2.1.3.min.js"></script>
		<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.1/js/bootstrap.min.js"></script>
		<script language="javascript" src="/static/script.js"></script>
	</head>
	<body>
<nav class="navbar navbar-inverse navbar-fixed-top" role="navigation">
      <div class="container">
        <div class="navbar-header">
          <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#navbar" aria-expanded="false" aria-controls="navbar">
            <span class="sr-only">Toggle navigation</span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </button>
          <a class="navbar-brand" href="/">Interest Link - ${heading}</a>
        </div>
        <div id="navbar" class="navbar-collapse collapse">
% if user:
          <ul class="nav navbar-nav navbar-right">
            <!--
            <li class="active"><a href="#">Home</a></li>
            <li><a href="#about">About</a></li>
            <li><a href="#contact">Contact</a></li>
            -->
            <!--
            <li class="dropdown">
              <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-expanded="false">Logged in as ${user.username} <span class="caret"></span></a>
              <ul class="dropdown-menu" role="menu">
                <li><a href="/user/logout">Log Out</a></li>
             -->
                <!--
                <li><a href="#">Another action</a></li>
                <li><a href="#">Something else here</a></li>
                <li class="divider"></li>
                <li class="dropdown-header">Nav header</li>
                <li><a href="#">Separated link</a></li>
                <li><a href="#">One more separated link</a></li>
                -->
              <!-- </ul>
            </li> -->
        <li><a>Logged in as ${user.username}</a></li>
	<li><a href="/friends">Friends
	% if user.friend_requests_incoming:
		(${len(user.friend_requests_incoming)} pending)
	% endif
		</a>
	</li>
                <li><a href="/user/logout">Log Out</a></li>
          </ul>
% else:
          <form class="navbar-form navbar-right" role="form" action="/user/login" method="POST">
            <div class="form-group">
              <input name="username" type="text" placeholder="Username" class="form-control">
            </div>
            <div class="form-group">
              <input name="password" type="password" placeholder="Password" class="form-control">
            </div>
            <button type="submit" class="btn btn-success">Sign in</button>
          </form>
% endif
        </div><!--/.navbar-collapse -->
      </div>
    </nav>
		${self.body()}
		<div id="footer">
			Link software by Shish
		</div>
	</body>
</html>
