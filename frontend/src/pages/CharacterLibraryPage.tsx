import React, { useState } from 'react';
import { Card, Button, Modal, Form, Input, Select, Typography, Row, Col, Tag, Spin, message, Empty } from 'antd';
import { PlusOutlined, PictureOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { charactersApi } from '@/api';
import type { Character } from '@/types';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;

export function CharacterLibraryPage() {
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [form] = Form.useForm();
  const qc = useQueryClient();

  const { data: characters, isLoading } = useQuery({
    queryKey: ['characters'],
    queryFn: charactersApi.listCharacters,
  });

  const createMutation = useMutation({
    mutationFn: (data: Partial<Character>) => charactersApi.createCharacter(data),
    onSuccess: () => { message.success('Character created!'); qc.invalidateQueries({ queryKey: ['characters'] }); setCreateModalOpen(false); form.resetFields(); },
    onError: (err: any) => message.error(err?.response?.data?.detail || 'Failed to create character'),
  });

  const generateImageMutation = useMutation({
    mutationFn: (id: number) => charactersApi.generateImage(id),
    onSuccess: () => { message.success('Character image generated!'); qc.invalidateQueries({ queryKey: ['characters'] }); },
    onError: () => message.error('Image generation failed'),
  });

  if (isLoading) return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>🎭 Character Library</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}
          style={{ background: '#ea580c', borderColor: '#ea580c' }}>
          Create Character
        </Button>
      </div>

      {!characters?.length ? (
        <Card>
          <Empty
            image="https://placehold.co/120x120/FFB347/FFF?text=🎭"
            description={
              <div>
                <Text strong>No characters yet</Text>
                <br />
                <Text type="secondary">Create original characters for your TinyTales World universe</Text>
              </div>
            }
          >
            <Button type="primary" onClick={() => setCreateModalOpen(true)}>Create First Character</Button>
          </Empty>
        </Card>
      ) : (
        <Row gutter={[16, 16]}>
          {characters.map(char => (
            <Col xs={24} sm={12} md={8} lg={6} key={char.id}>
              <Card
                hoverable
                cover={
                  char.reference_image_url ? (
                    <img alt={char.name} src={char.reference_image_url} style={{ height: 200, objectFit: 'cover' }} />
                  ) : (
                    <div style={{ height: 200, background: 'linear-gradient(135deg, #fed7aa, #fbbf24)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <span style={{ fontSize: 64 }}>🎨</span>
                    </div>
                  )
                }
                actions={[
                  <Button
                    key="img" type="text" icon={<PictureOutlined />} size="small"
                    loading={generateImageMutation.isPending}
                    onClick={() => generateImageMutation.mutate(char.id)}
                  >
                    {char.reference_image_url ? 'Regenerate' : 'Generate Image'}
                  </Button>,
                ]}
              >
                <Card.Meta
                  title={char.name}
                  description={
                    <div>
                      <Tag color={char.character_type === 'main' ? 'orange' : 'blue'} style={{ marginBottom: 4 }}>
                        {char.character_type}
                      </Tag>
                      <Paragraph ellipsis={{ rows: 2 }} style={{ margin: 0, fontSize: 12 }}>
                        {char.description}
                      </Paragraph>
                    </div>
                  }
                />
              </Card>
            </Col>
          ))}
        </Row>
      )}

      <Modal
        title="Create New Character"
        open={createModalOpen}
        onCancel={() => { setCreateModalOpen(false); form.resetFields(); }}
        footer={null}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={createMutation.mutate}>
          <Form.Item name="name" label="Character Name" rules={[{ required: true }]}>
            <Input placeholder="e.g. Sunny the Sunflower" />
          </Form.Item>
          <Form.Item name="character_type" label="Type" initialValue="main">
            <Select>
              <Option value="main">Main Character</Option>
              <Option value="supporting">Supporting Character</Option>
              <Option value="background">Background Character</Option>
              <Option value="narrator">Narrator</Option>
            </Select>
          </Form.Item>
          <Form.Item name="description" label="Description" rules={[{ required: true }]}>
            <TextArea rows={3} placeholder="Who is this character? What is their role?" />
          </Form.Item>
          <Form.Item name="appearance" label="Appearance" rules={[{ required: true }]}>
            <TextArea rows={3} placeholder="Describe their visual appearance in detail for image generation" />
          </Form.Item>
          <Form.Item name="personality" label="Personality">
            <Input placeholder="e.g. Cheerful, curious, loves to teach" />
          </Form.Item>
          <Form.Item name="image_generation_prompt" label="Image Generation Prompt (optional)">
            <TextArea rows={2} placeholder="Detailed prompt for AI image generation (leave blank for auto-generated)" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={createMutation.isPending} block
              style={{ background: '#ea580c', borderColor: '#ea580c' }}>
              Create Character
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
