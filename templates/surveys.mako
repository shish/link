<%inherit file="base.mako"/>

<div class="col-md-5">
    % if user:
        <h3>Lists</h3>
        <ul>
            % for survey in surveys:
                <li>
                    <a href="/survey/${survey.id}">${survey.name} - ${survey.description}</a>
                    <!-- [${survey.user.username}] -->
                    % for response in responses:
                        % if response.survey == survey:
                            <%
                            line = ""
                            new_count = len(survey.questions) - len(response.answers)
                            if new_count:
                                line += "%d recently added" % new_count

                            friend_count = 0
                            other_count = 0
                            for r in survey.responses:
                                if r.user in user.all_friends:
                                    friend_count += 1
                                else:
                                    other_count += 1
                            if line and (friend_count or other_count):
                                line += ", "
                            if friend_count and other_count:
                                line += "%d friends and %d others responded" % (friend_count, other_count)
                            elif friend_count:
                                line += "%d friends responded" % friend_count
                            elif other_count:
                                line += "%d others responded" % other_count
                            %>
                            % if line:
                                <br>(${line})
                            % endif
                        % endif
                    % endfor
                </li>
            % endfor
        </ul>
    % else:
        <div class="d-lg-none">
            <h3 name="login">Sign In</h3>
            <form action="/user/login" method="POST">
                <input class="form-control" type="text" name="username" placeholder="Username">
                <input class="form-control" type="password" name="password" placeholder="Password">
                <input class="btn btn-primary col-md-12" type="submit" value="Sign In">
            </form>
        </div>

        <h3>Create Account</h3>
        <form action="/user/create" method="POST">
            <input class="form-control" type="text" name="username" placeholder="Username">
            <input class="form-control" type="password" name="password1" placeholder="Password">
            <input class="form-control" type="password" name="password2" placeholder="Repeat Password">
            <input class="form-control" type="text" name="email" placeholder="Email (Optional)">
            <input class="btn btn-primary col-md-12" type="submit" value="Create">
        </form>

        <p><h3>Latest Lists</h3>
        <ul>
            % for survey in surveys:
                <li>
                    ${survey.name} - ${survey.description} (${len(survey.responses)} responses)
                </li>
            % endfor
        </ul>
    % endif
</div>

<div class="col-md-7">
    <h3>About</h3>
    <p>How this site works:</p>
    <ol>
        <li>You say what you like.
        <li>Your friends say what they like.
        <li>The site tells you what you have in common.
    </ol>

    <h3>Why?</h3>
    <p>
        Say I have a terrible secret that I like singing along to S-Club 7, which
        I will never admit to in public. If any of my friends are also into that, then we
        can find each other and have secret S-Club karaoke sessions. My other friends who
        don't like S-Club will never know :D
    </p>
    <p>
        This isn't foolproof; somebody could claim to like everything just to see what
        matches they get - but if one of your friends does that, you should punch them
        in the face until they stop doing that :3
    </p>
</div>
