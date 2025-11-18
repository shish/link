import { faCircleInfo } from "@fortawesome/free-solid-svg-icons";
import { Tooltip } from "react-tooltip";
import { FontAwesomeIcon } from "./FontAwesomeIcon";
import css from "./Tip.module.scss";

export function Tip({ text }: { text: string }): React.ReactElement {
    const id = text.replace(/[^a-zA-Z0-9]/g, "_");
    return (
        <>
            {" "}
            <FontAwesomeIcon
                icon={faCircleInfo}
                className={css.tip}
                data-tooltip-id={id}
                data-tooltip-content={text}
            />
            <Tooltip id={id} />
        </>
    );
}
