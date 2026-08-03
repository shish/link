import { type Comparison, Www } from "../gql/graphql";

export function CompareSection({
    section,
    comparisons,
}: {
    section: string;
    comparisons: Array<Comparison>;
}) {
    function compsort(a: Comparison, b: Comparison) {
        const s = {
            'WANT': 2,
            'WILL': 1,
            'WONT': 0,
            'NA': 0,
        };
        return (
            s[b.mine] + s[b.theirs] - (s[a.mine] + s[a.theirs]) ||
            a.order - b.order
        );
    }

    return (
        <>
            <h3>{section}</h3>
            <ul>
                {comparisons.sort(compsort).map((c) => (
                    <ComparisonEl key={c.text + c.order} comparison={c} />
                ))}
            </ul>
        </>
    );
}

function ComparisonEl({ comparison }: { comparison: Comparison }) {
    const c = comparison;

    if (c.mine === 'WANT' && c.theirs === 'WANT') {
        if (!c.flip) {
            return (
                <li>
                    <b>You both want {c.text}</b>
                </li>
            );
        } else {
            return (
                <li>
                    <b>
                        You want {c.text} and they want {c.flip}
                    </b>
                </li>
            );
        }
    } else if (c.mine === 'WANT' && c.theirs === 'WILL') {
        return (
            <li>
                You want {c.flip ? c.text : ""} and they would try{" "}
                {c.flip ? c.flip : c.text}
            </li>
        );
    } else if (c.mine === 'WILL' && c.theirs === 'WANT') {
        return (
            <li>
                You would try {c.flip ? c.text : ""} and they want{" "}
                {c.flip ? c.flip : c.text}
            </li>
        );
    } else {
        return "Err??";
    }
}
