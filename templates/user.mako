<%inherit file="base.mako"/>

<div class="col-md-12">
    <h3>Settings</h3>
    <form action="/user" method="POST">
        <input type="hidden" name="csrf_token" value="${user.token}">
        <input type="password" class="form-control" name="old_password" value="" placeholder="Current Password">
        <input type="text" class="form-control" name="new_username" value="${user.username}" placeholder="Username">
        <input type="password" class="form-control" name="new_password_1" value="" placeholder="New Password">
        <input type="password" class="form-control" name="new_password_2" value="" placeholder="Repeat New Password">
        <input type="email" class="form-control" name="new_email" value="${user.email or ''}" placeholder="Email (Optional)">
        <input class="btn btn-primary col-md-12" type="submit" value="Save Settings">
    </form>
</div>
