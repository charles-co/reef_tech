import asyncio
import multiprocessing as mp

import aiohttp
import pandas as pd
import requests

from config import get_config, get_previous_day, logger


class Connector:
    """
    Connector class to fetch data from the API
    """

    def __init__(self):
        self.config = get_config()
        self.session = requests.Session()
        self.session.headers.update({"AppToken": self.config["app_token"]})
        self.base_url = self.config["base_url"]
        self.auth_token = {"auth_token": self.config["auth_token"]}
        self.organizations = {}
        self.activities = mp.Manager().dict()

    def get_groups(self, page=0):
        path = "/v109/groups"
        self.session.headers.update({"PageStartId": str(page)})
        resp = self.session.get(self.base_url + path, params=self.auth_token)
        resp.raise_for_status()

        data = resp.json()

        self.organizations = {
            organization["id"]: organization["name"]
            for organization in data["organizations"]
        }

        # if page size limit is exceeded, fetch next page

        if "pagination" in data and data["pagination"]["next_page_start_id"] > page:
            self.get_groups(data["pagination"]["next_page_start_id"])

    async def get_activities(
        self,
    ):

        async with aiohttp.ClientSession() as session:
            session.headers.update(
                dict(self.session.headers)
                | {"DateStart": get_previous_day(), "include": "projects,users"}
            )
            tasks = []
            for id, name in self.organizations.items():
                task = asyncio.create_task(self._fetch_activity(session, id, name))
                tasks.append(task)

            await asyncio.gather(*tasks)

    async def _fetch_activity(self, session: aiohttp.ClientSession, id: str, name: str):

        path = "/v109/groups/{org_id}/actions/day"
        page = 0

        while True:
            session.headers.update({"PageStartId": str(page)})
            async with session.get(
                self.base_url + path.format(org_id=id),
                params=self.auth_token | {"date[stop]": get_previous_day()},
            ) as resp:
                if resp.status != 200:
                    logger.error(f"Failed to get activities for {name}")
                    return

                data = await resp.json()

                if name in self.activities:
                    self.activities[name]["daily_activities"].extend(
                        data["daily_activities"]
                    )
                else:
                    self.activities[name] = data

                if (
                    "pagination" in data
                    and (next_page_id := data["pagination"]["next_page_start_id"])
                    > page
                ):
                    page = next_page_id
                    continue
                else:
                    break

    def parse_activities_to_html(
        self,
    ):
        with mp.Pool() as pool:
            html_tables = pool.map(self._parse_activity, self.activities.keys())
        return dict(html_tables)

    def _parse_activity(self, org_name: str):

        daily_activities_df = pd.DataFrame(
            self.activities[org_name]["daily_activities"],
            columns=[
                "id",
                "project_id",
                "user_id",
                "date",
                "task_id",
                "tracked",
            ],
        )

        users_df = pd.DataFrame(
            self.activities[org_name]["users"],
            columns=[
                "id",
                "name",
                "email",
                "status",
            ],
        )
        projects_df = pd.DataFrame(
            self.activities[org_name]["projects"],
            columns=[
                "id",
                "name",
                "status",
            ],
        )

        df = (
            daily_activities_df.groupby(["user_id", "project_id"])
            .agg({"tracked": "sum"})
            .reset_index()
        )
        df["tracked"] = df["tracked"].apply(lambda x: round(x / 3600, 2))

        df = df.merge(
            users_df.rename(columns={"id": "user_id"}), on="user_id", how="left"
        ).merge(
            projects_df.rename(
                columns={
                    "id": "project_id",
                    "name": "project_name",
                    "status": "project_status",
                }
            ),
            on="project_id",
            how="left",
        )
        df["formatted_name"] = df["name"] + " - " + df["email"]
        df["tracked"] = df["tracked"].astype(str) + " hr"

        df = df[["formatted_name", "project_name", "tracked"]]

        return (
            org_name,
            df.pivot_table(
                values="tracked",
                index="formatted_name",
                columns="project_name",
                aggfunc=lambda x: " ".join(x),
            ).to_dict("split"),
        )

    def send_email(self, html_tables: dict):
        ...

    def run(self):

        try:
            self.get_groups()
            asyncio.run(self.get_activities())
            html_tables = self.parse_activities_to_html()
        except Exception as e:
            # TODO: log error or notify via slack API
            logger.error(e)

        return html_tables
