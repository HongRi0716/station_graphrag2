import { getServerApi } from '@/lib/api/server';
import { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';
import { redirect } from 'next/navigation';
import { SignUpForm } from './signup-form';

export async function generateMetadata(): Promise<Metadata> {
  const page_auth = await getTranslations('page_auth');
  return {
    title: page_auth('signup'),
  };
}

type Props = {
  searchParams: Promise<{ callbackUrl?: string }>;
};

export default async function Page({ searchParams }: Props) {
  const apiServer = await getServerApi();

  try {
    const res = await apiServer.defaultApi.userGet();
    if (res.data) {
      const { callbackUrl } = await searchParams;
      redirect(callbackUrl || '/workspace');
    }
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
  } catch (err) {}

  return <SignUpForm />;
}
