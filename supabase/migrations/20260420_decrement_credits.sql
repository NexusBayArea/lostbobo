create or replace function decrement_credits(user_id uuid, amount int)
returns void as $$
begin
  update profiles
  set credit_balance = credit_balance - amount
  where id = user_id;
end;
$$ language plpgsql;
