document.addEventListener(
    "DOMContentLoaded",
    function () {

        const menuButton =
            document.getElementById(
                "menuButton"
            );

        const sidebar =
            document.getElementById(
                "sidebar"
            );


        if (
            menuButton &&
            sidebar
        ) {

            menuButton.addEventListener(
                "click",
                function () {

                    sidebar.classList.toggle(
                        "open"
                    );

                }
            );

        }

    }
);