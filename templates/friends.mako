<%inherit file="base.mako"/>

<style>
    .zebra {
        width: 100%;
    }

    .zebra TD:first-child {
        width: 66%;
    }

    .zebra INPUT {
        width: 100%;
    }
</style>

<div class="col-md-4">
    <h3>Confirmed</h3>
    <table class="zebra">
        % for friend in user.all_friends:
            <tr>
                <td>${friend.username}</td>
                <td><form action="/friends" method="POST">
                    <input type="hidden" name="_method" value="DELETE">
                    <input type="hidden" name="their_name" value="${friend.username}">
                    <input type="submit" value="Remove">
                </form></td>
            </tr>
        % endfor
    </table>
</div>

<div class="col-md-4">
    <h3>Sent Requests</h3>
    <table class="zebra">
        % for request in user.friend_requests_sent:
            <tr>
                <td>${request.friend_b.username}</td>
                <td><form action="/friends" method="POST">
                    <input type="hidden" name="_method" value="DELETE">
                    <input type="hidden" name="their_name" value="${request.friend_b.username}">
                    <input type="submit" value="Cancel">
                </form></td>
            </tr>
        % endfor
            <tr>
                <form action="/friends" method="POST">
                <td>
                    <input type="text" name="their_name" placeholder="Their username">
                </td>
                <td>
                    <input type="submit" value="Send Request">
                </td>
                </form>
            </tr>
    </table>

    <h3>Suggested</h3>
    <%
    req_users = [req.friend_b for req in user.friend_requests_sent] + [req.friend_a for req in user.friend_requests_incoming]
    recommended_d = {}
    for f in user.all_friends:  # for all friends
        for ff in f.all_friends:  # for all friends of friends
            # if the FoF is not already a friend, or a requested friend, or the user themselves
            if ff in user.all_friends or ff in req_users or ff == user:
                continue
            # increment their counter
            if ff not in recommended_d:
                recommended_d[ff] = 0
            recommended_d[ff] += 1

    recommended = []
    for key, value in recommended_d.items():
        recommended.append((value, key))
    %>
    <table class="zebra">
        % for n, friend in reversed(sorted(recommended)):
            <tr>
                <td>
                    ${friend.username} (${n} mutual)
                </td>
                <td>
                    <form action="/friends" method="POST">
                        <input type="hidden" name="their_name" value="${friend.username}">
                        <input type="submit" value="Send Request">
                    </form>
                </td>
            </tr>
        % endfor
    </table>
</div>

<div class="col-md-4">
    <h3>Incoming Requests</h3>
    <table class="zebra">
        % for request in user.friend_requests_incoming:
            <tr>
                <td>${request.friend_a.username}</td>
                <td><form action="/friends" method="POST">
                    <input type="hidden" name="their_name" value="${request.friend_a.username}">
                    <input type="submit" value="Accept">
                </form></td>
                <td><form action="/friends" method="POST">
                    <input type="hidden" name="_method" value="DELETE">
                    <input type="hidden" name="their_name" value="${request.friend_a.username}">
                    <input type="submit" value="Decline">
                </form></td>
            </tr>
        % endfor
    </table>
</div>
