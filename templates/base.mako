<!doctype html>
<html>
	<head>
		<meta charset="utf-8">
		<meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
		<title>Interest Link - ${heading}</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.2/css/bootstrap.min.css" integrity="sha384-Smlep5jCw/wG7hdkwQ/Z5nLIefveQRIY9nfy6xoR1uRYBtpZgI6339F5dgvm/e9B" crossorigin="anonymous">
        <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.6.3/css/all.css" integrity="sha384-UHRtZLI+pbxtHCWp1t77Bi1L4ZtiqrqD80Kn4Z8NTSRyMA2Fd33n5dQ8lWUE00s/" crossorigin="anonymous">
		<link rel="stylesheet" href="/static/style.css">

		<link rel="icon" type="image/x-icon" href="/static/favicon.ico">
	</head>
	<body class="">
        <script language="javascript" src="/static/light_dark.js"></script>
        <nav class="navbar navbar-expand-lg navbar-dark fixed-top bg-dark" role="navigation">
            <a class="navbar-brand" href="/">Interest Link - ${heading}</a>
            <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarCollapse" aria-controls="navbarCollapse" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div id="navbarCollapse" class="navbar-collapse collapse">
            % if user:
                <ul class="navbar-nav ml-auto">
                    <li class="nav-item"><a class="nav-link" href="/user">Logged in as ${user.username}</a></li>
                    <li class="nav-item"><a class="nav-link" href="/friends">Friends
                        % if user.friend_requests_incoming:
                            (${len(user.friend_requests_incoming)} pending)
                        % endif
                    </a></li>
                    <li class="nav-item"><a class="nav-link" href="/user/logout">Log Out</a></li>
                </ul>
            % else:
                <form class="form-inline ml-auto mt-2 mt-lg-0" role="form" action="/user/login" method="POST">
                    <input name="username" type="text" placeholder="Username" class="form-control mr-sm-2">
                    <input name="password" type="password" placeholder="Password" class="form-control mr-sm-2">
                    <button type="submit" class="btn btn-outline-success my-2 my-sm-0">Sign In</button>
                </form>
            % endif
            </div><!--/.navbar-collapse -->
        </nav>
        <main role="main" class="container" style="margin-top: 71px">
            <div class="row">
                ${self.body()}
            </div>
        </main>
		<footer class="container">
            <p>
                <a href="https://github.com/shish/link">Link software</a>
                by <a href="https://shish.io/">Shish</a>
            </p>
		</footer>
        <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js" integrity="sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49" crossorigin="anonymous"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.2/js/bootstrap.min.js" integrity="sha384-o+RDsa0aLu++PJvFqy8fFScvbHFLtbvScb8AjopnFD+iEQ7wo/CG0xlczd+2O/em" crossorigin="anonymous"></script>
		<script language="javascript" src="/static/script.js"></script>
	</body>
</html>
