<%inherit file="base.mako"/>

<div id="body" class="container">
	<div class="row">
		<div class="col-md-4">
			<form action="/user" method="POST">
			
				<input type="hidden" name="csrf_token" value="${user.token}">

<table>
	<tr>
		<td>Current Password</td>
		<td><input type="password" name="old_password" value=""></td>
	</tr>
	<tr>
		<td>Username</td>
		<td><input type="text" name="new_username" value="${user.username}"></td>
	</tr>
	<tr>
		<td>New Password</td>
		<td><input type="password" name="new_password_1" value=""></td>
	</tr>
	<tr>
		<td>Repeat Password</td>
		<td><input type="password" name="new_password_2" value=""></td>
	</tr>
	<tr>
		<td>Email</td>
		<td><input type="text" name="new_email" value="${user.email or ''}"></td>
	</tr>
	<tr>
		<td colspan="2"><input type="submit" value="Send Request"></td>
	</tr>
</table>

			</form>

		</div>
	</div>
</div>
