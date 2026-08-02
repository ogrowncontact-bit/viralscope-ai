import { UserButton } from "@clerk/nextjs";

export function UserMenu() {
  return (
    <UserButton
      appearance={{
        elements: { avatarBox: "size-8" },
      }}
    />
  );
}
