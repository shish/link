<%inherit file="base.mako"/>

<div class="col-md-9">
    <h3 style="display:inline">Comparing answers for <a href="/survey/${survey.id}">${survey.name}</a>
        % if theirs.privacy == "public" or theirs.privacy == "friends":
            with ${theirs.user.username}
        % else:
            with [hidden]
        % endif
    </h3>
    <form action="/response/${theirs.id}" method="GET" style="display:inline">
        <label for="sort_by">Sorted by: </label>
        <select name="sort_by" onchange="javascript:document.forms[0].submit()">
            <option value="" ${"selected" if sort_by == "" else ""}>Compatibility</option>
            <option value="cat" ${"selected" if sort_by == "cat" else ""}>Category</option>
        </select>
    </form>
    <p>${survey.long_description or ""}</p>

    <%
    things = []
    for my_answer in response.answers:
        for their_answer in theirs.answers:
            if my_answer.question.matches(their_answer.question):
                score = my_answer.value + their_answer.value
                if score > 2:
                    if my_answer.question == their_answer.question:
                        if my_answer.value == their_answer.value:
                            thing = 'You both %s "%s"' % (
                                my_answer.value_name(), my_answer.question.text
                            )
                        else:
                            thing = 'You %s / they %s "%s"' % (
                                my_answer.value_name(),
                                their_answer.value_name(), my_answer.question.text
                            )
                    else:
                        thing = 'You %s "%s" and they %s "%s"' % (
                            my_answer.value_name(), my_answer.question.text,
                            their_answer.value_name(), their_answer.question.text
                        )
                    things.append({
                        "score": -score, 
                        "their_score": -their_answer.value, 
                        "order": my_answer.question.order, 
                        "thing": thing, 
                        "section": my_answer.question.section
                    })
    %>
    <% 
        def sort_order(row):
            if sort_by == "cat": 
                return (row["section"], row["score"], row["their_score"], row["order"])
            else:
                return (row["score"], row["their_score"], row["order"])
        last_section = None 
    %>
    <ul>
        % for row in sorted(things, key=sort_order):
            % if sort_by == "cat" and last_section != row["section"]:
                </ul><h4>${row["section"] if row["section"] else "Unsorted"}</h4><ul>
            % endif
            % if -row["score"] == 4:
                <li><b>${row["thing"]}</b></li>
            % else:
                <li>${row["thing"]}</li>
            % endif
            <% last_section = row["section"] %>
        % endfor
    </ul>
</div>

<div class="col-md-3">
    <h3>Links</h3>
    % if friends:
        <p>Friends who did this:
        <ul>
            % for fresponse in friends:
                <li><a href="/response/${fresponse.id}">${fresponse.user.username}</a></li>
            % endfor
        </ul>
    % endif

    % if others:
        <p>Other people who did this:
        <ul>
            % for oresponse in others:
                <li><a href="/response/${oresponse.id}">${oresponse.user.username}</a></li>
            % endfor
        </ul>
    % endif
</div>
