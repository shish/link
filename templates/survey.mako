<%inherit file="base.mako"/>
<%
def checkedIf(b):
    return 'checked="checked"' if b else ""

def selectedIf(b):
    return 'selected="selected"' if b else ""
%>

<datalist id="sections">
    % for section in sorted(survey.sections):
        <option value="${section}">${section or "Unsorted"}</option>
    % endfor
</datalist>


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
                <input type="radio" name="privacy" value="friends"
                    ${checkedIf(response and response.privacy=="friends")|n}>
                Friends Only (Friends can see, others can't)
            </label>
            <br><label>
                <input type="radio" name="privacy" value="hidden"
                    ${checkedIf(response and response.privacy=="hidden")|n}>
                Hidden (Response will only be given an ID number and not visibly linked to an account)
            </label>
            <br><label>
                <input type="radio" name="privacy" value="public"
                    ${checkedIf(response and response.privacy=="public")|n}>
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
                    <a data-toggle="tooltip"
                       data-original-title="Want to do / Will try for somebody else's benefit / Won't do"
                    ><i class="fas fa-info-circle"></i></a>
                </th>
            </tr>
            </thead>
            <tbody>
            <%
            last_section = None
            %>
        	% for question, prev in zip(survey.contents, [None]+survey.contents):
                % if question.section != last_section:
                    <%
                    last_section = question.section
                    %>
                    </tbody>
                    <thead>
                        <tr>
                            <th colspan="2" data-toggle="collapse" href="#s${question.id}">
                                ${question.section or "Unsorted"}
                            </th>
                        </tr>
                    </thead>
                    <!-- <tbody class="collapse" id="s${question.id}"> -->
                    <tbody id="s${question.id}">
        		% endif:
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
                    % if question.is_second_of_pair:
                        &nbsp;&nbsp;&rarr;
                    % endif
                    ${question.text}
                    % if question.extra:
                        <a data-toggle="tooltip"
                            data-original-title="${question.extra}"
                        ><i class="fas fa-info-circle"></i></a>
                    % endif
                    </td>
                    <td class="www">
                        <label class="want">
                            Yay!
                            <input type="radio" name="q${question.id}"
                                    value="2" ${checkedIf(val == 2)|n}>
                        </label>
                        <label class="will">
                            <input type="radio" name="q${question.id}"
                                    value="1" ${checkedIf(val == 1)|n}>
                        </label>
                        <label class="wont">
                            <input type="radio" name="q${question.id}"
                                    value="-2" ${checkedIf(val == -2)|n}>
                            Boo!
                        </label>
                        <br class="d-block d-xl-none d-lg-none d-md-none d-sm-none">
                        <label>
                            (N/A
                            <input type="radio" name="q${question.id}"
                                    value="0" ${checkedIf(val == 0)|n}>)
                        </label>
                    </td>
                </tr>
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
        <input class="form-control" type="text" name="section" placeholder="Section" list="sections">
        <input class="form-control" type="text" name="q1" placeholder="Question" required="required">
        <input class="form-control" type="text" name="q2" placeholder="Paired opposite (optional)">
        <input class="form-control" type="text" name="q1extra" placeholder="Extra description for Q1">
        <input class="btn btn-primary col-md-12" type="submit" value="Add Question">
    </form>
</div>

