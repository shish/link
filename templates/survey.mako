<%inherit file="base.mako"/>
<%
def checkedIf(b):
    return 'checked="checked"' if b else ""

def selectedIf(b):
    return 'selected="selected"' if b else ""
%>

<div class="col-md-9">

    <h3>${survey.description}</h3>
    <p>${survey.long_description or ""}</p>

    % if response:
        <p>Give this link to someone so they can compare with you
        (they'll be prompted to fill in their answers first if they haven't already):
        <a href="${link}">${link}</a></p>
    % endif

    <form action="/response" method="POST">
        <input type="hidden" name="survey" value="${survey.id}">
        % if compare:
            <input type="hidden" name="compare" value="${compare}">
        % endif
        <p>
            Privacy:
            <br><label>
                <input type="radio" name="privacy" value="friends" ${checkedIf(response and response.privacy=="friends")|n}>
                Friends Only (Friends can see, others can't)
            </label>
            <br><label>
                <input type="radio" name="privacy" value="hidden" ${checkedIf(response and response.privacy=="hidden")|n}>
                Hidden (Response will only be given an ID number and not visibly linked to an account)
            </label>
            <br><label>
                <input type="radio" name="privacy" value="public" ${checkedIf(response and response.privacy=="public")|n}>
                Public (Show up in the list of people who answered)
            </label>
        </p>

        <p id="jscontrols"></p>

        <table class="zebra" style="width: 100%;">
            <thead>
            <tr>
                <th>Thing</th>
                <th style="text-align: right;">
                    Want / Will / Won't
                    <a data-toggle="tooltip" data-original-title="Want to do / Will try for somebody else's benefit / Won't do (with the right person / conditions / etc, in each case)">(?)</a>
                </th>
            </tr>
            </thead>
            <tbody>
            <%
            prev = None
            %>
        	% for question in survey.contents:
                % if question.entry_type == "heading":
                    <%
                    hid = question.text.replace(' ', '')
                    %>
                    </tbody>
                    <thead>
                        <tr>
                            <th colspan="2" data-toggle="collapse" href="#s${hid}">
                                ${question.text}
                            </th>
                        </tr>
                    </thead>
                    <!-- <tbody class="collapse" id="s${hid}"> -->
                    <tbody id="s${hid}">
        		% else:
                    <%
                    val = response.value(question.id) if response else 0
                    %>
                    <tr id="q${question.id}" class="answer a${val}">
                        <td>
                        % if survey.user == user:
                        ##	${question.id} - ${question.order}
                            <a href="/question/${question.id}/up">&uarr;</a>
                            <a href="/question/${question.id}/down">&darr;</a>
                        ##	<a href="/question/${question.id}/remove">X</a>
                        % endif
                        % if question.flip and question.flip == prev:
                            &nbsp;&nbsp;&rarr;
                        % endif
                        ${question.text}
                        % if question.extra:
                            <a data-toggle="tooltip" data-original-title="${question.extra}">(?)</a>
                        % endif
                        </td>
                        <td class="www">
                            <label class="want">
                                Yay!
                                <input type="radio" name="q${question.id}" value="2" ${checkedIf(val == 2)|n}>
                            </label>
                            <label class="will">
                                <input type="radio" name="q${question.id}" value="1" ${checkedIf(val == 1)|n}>
                            </label>
                            <label class="wont">
                                <input type="radio" name="q${question.id}" value="-2" ${checkedIf(val == -2)|n}>
                                Boo!
                            </label>
                            <br class="d-block d-xl-none d-lg-none d-md-none d-sm-none">
                            <label>
                                (N/A
                                <input type="radio" name="q${question.id}" value="0" ${checkedIf(val == 0)|n}>)
                            </label>
                        </td>
                    </tr>
                    <%
                    prev = question
                    %>
                % endif
	        % endfor
    	    </tbody>
        </table>
        <input class="btn btn-primary col-md-12" type="submit" value="Save Answers">
    </form>
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

    % if response:
        <form action="/response/${response.id}" method="POST">
            <input type="hidden" name="_method" value="DELETE">
            <input type="submit" class="btn btn-danger" value="Delete My Answers">
        </form>
    % endif

    % if survey.user == user:
        <form action="/survey/${survey.id}" method="POST">
            <input type="submit" class="btn btn-secondary" value="Set Order">
        </form>
    % endif
</div>

<div class="col-md-12">
    <h3>Add Question</h3>
    <form action="/question" method="POST">
        <input type="hidden" name="survey" value="${survey.id}">
        <select class="form-control" name="heading">
            <option value="-1">Add to end</option>
        % for heading in sorted(survey.headings):
            <option value="${heading.id}">${heading.text}</option>
        % endfor
            <option value="-2">Add as heading</option>
        </select>
        <input class="form-control" type="text" name="q1" placeholder="Question" required="required">
        <input class="form-control" type="text" name="q2" placeholder="Paired opposite (optional)">
        <input class="form-control" type="text" name="q1extra" placeholder="Extra description for Q1">
        <input class="btn btn-primary col-md-12" type="submit" value="Add Question">
    </form>
</div>

