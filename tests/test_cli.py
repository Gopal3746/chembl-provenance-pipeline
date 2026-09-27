from drug_catalog.cli import build_parser


def test_run_command_parses_target() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "run",
            "--target",
            "CHEMBL203",
            "--max-records",
            "25",
        ]
    )

    assert args.command == "run"
    assert args.target == "CHEMBL203"
    assert args.max_records == 25
